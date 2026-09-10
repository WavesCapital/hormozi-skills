"""Native Word blocks supplement, never replace, the converted page record.

Preserve table cells, direct revision/strike marks, links, and original media.
Word layout and list counters are not simulated: retain their source metadata
and warn where a rendered page is needed. The caller owns staging/promotion.
"""
from __future__ import annotations

import hashlib
import io
import json
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def local(node: ET.Element) -> str:
    return node.tag.rsplit('}', 1)[-1]


def xml(data: bytes) -> ET.Element:
    if b'\x00' in data:
        raise ValueError('Word XML must be UTF-8')
    text = data.decode('utf-8-sig')
    if '<!ENTITY' in text.upper() or '<!DOCTYPE' in text.upper():
        raise ValueError('Word entity/doctype declarations are unsupported')
    return ET.fromstring(text)


def member(base: str, target: str) -> str:
    parsed = urlsplit(target)
    decoded = unquote(parsed.path)
    if parsed.scheme or parsed.netloc or parsed.query or '\\' in decoded or '\x00' in decoded or decoded.startswith('/'):
        raise ValueError('Word relationship must be a local archive member')
    result = posixpath.normpath(posixpath.join(posixpath.dirname(base), decoded))
    if result in {'', '.', '..'} or result.startswith('../'):
        raise ValueError('Word relationship escapes archive')
    return result


def on(properties: ET.Element | None, name: str) -> bool:
    element = properties.find(f'{{{W}}}{name}') if properties is not None else None
    return element is not None and element.get(f'{{{W}}}val', 'true').lower() not in {'0', 'false', 'off'}


def extract(source: dict, original: Path, derived_root: Path) -> tuple[list[dict], dict]:
    raw = original.read_bytes()
    if sha(raw) != source['sha256']:
        raise ValueError('Word original hash mismatch')
    root = derived_root.resolve()
    source_slug = re.sub(r'[^a-zA-Z0-9_-]', '-', source['source_id'])
    asset_dir = root / 'docx-assets' / source_slug
    if not asset_dir.resolve().is_relative_to(root):
        raise ValueError('Word asset path escapes staging')
    records, assets = [], []
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or sum(info.file_size for info in archive.infolist()) > 256 * 1024 * 1024:
            raise ValueError('Duplicate or oversized Word archive')
        part = 'word/document.xml'
        document_bytes = archive.read(part)
        document = xml(document_bytes)
        body = document.find(f'{{{W}}}body')
        if body is None:
            raise ValueError('Word document has no main body')
        paragraphs = list(document.iter(f'{{{W}}}p'))
        paragraph_indices = {id(p): i for i, p in enumerate(paragraphs)}
        table_indices = {id(t): i + 1 for i, t in enumerate(document.iter(f'{{{W}}}tbl'))}
        relationships = {}
        rel_name = 'word/_rels/document.xml.rels'
        if rel_name in names:
            for rel in xml(archive.read(rel_name)):
                key = rel.get('Id')
                if not key or key in relationships:
                    raise ValueError('Missing or duplicate Word relationship identity')
                external = rel.get('TargetMode') == 'External'
                relationships[key] = {'id': key, 'type': rel.get('Type'), 'external': external,
                                      'target': rel.get('Target') if external else member(part, rel.attrib['Target'])}
        # Every embedded media asset survives even if a layout-specific drawing
        # cannot be mapped to a body block. File names never control output paths.
        by_member = {}
        for name in names:
            if not name.startswith('word/media/') or name.endswith('/'):
                continue
            data = archive.read(name)
            suffix = Path(name).suffix.lower()
            if not re.fullmatch(r'\.[a-z0-9]{1,8}', suffix):
                suffix = '.bin'
            destination = asset_dir / (sha(data) + suffix)
            if not destination.resolve().is_relative_to(root):
                raise ValueError('Word media path escapes staging')
            asset = {'member': name, 'path': str(destination.relative_to(root)), 'sha256': sha(data), 'byte_size': len(data)}
            assets.append(asset)
            by_member[name] = asset
        part_hashes = {name: sha(archive.read(name)) for name in
                       (part, rel_name, 'word/styles.xml', 'word/numbering.xml') if name in names}
        # Inherited style/list rendering is deliberately not guessed. The full
        # metadata and original remain available alongside converted pages.
        style_meaning = []
        if 'word/styles.xml' in names:
            styles = xml(archive.read('word/styles.xml'))
            for style in styles.findall(f'{{{W}}}style'):
                if any(local(n) in {'strike', 'dstrike', 'vanish', 'webHidden'} for n in style.iter()):
                    style_meaning.append(style.get(f'{{{W}}}styleId'))

        for block_number, block in enumerate(body, 1):
            if local(block) == 'sectPr':
                continue
            warnings, links, images, lists, tables = set(), [], [], [], []
            if style_meaning:
                warnings.add('Inherited style marks need the original or converted visual; direct marks below are explicit only.')

            def render(node):
                tag = local(node)
                if node.tag in {f'{{{W}}}t', f'{{{W}}}delText'} or tag == 't' and node.tag.startswith('{http://schemas.openxmlformats.org/drawingml/'):
                    return node.text or ''
                if tag in {'pPr', 'rPr', 'tblPr', 'tcPr', 'trPr', 'tblGrid', 'sectPr'}:
                    return ''
                if tag in {'br', 'cr'}:
                    return '\n'
                if tag == 'tab':
                    return '\t'
                if tag == 'instrText':
                    warnings.add('Field instructions retained in the original; displayed field results are extracted.')
                    return ''
                if tag == 'AlternateContent':
                    choice = next((n for n in node if local(n) == 'Choice'), None)
                    if choice is None:
                        choice = next((n for n in node if local(n) == 'Fallback'), None)
                    warnings.add('Alternate drawing uses one branch; inspect the linked image for layout meaning.')
                    return render(choice) if choice is not None else ''
                if tag in {'blip', 'imagedata'}:
                    key = node.get(f'{{{R}}}embed') or node.get(f'{{{R}}}id') or node.get(f'{{{R}}}link')
                    rel = relationships.get(key)
                    if rel is None:
                        warnings.add('Drawing relationship missing; inspect the original.')
                        return '[Drawing with unresolved source]'
                    if rel['external']:
                        links.append(rel)
                        return '[External image: not fetched]'
                    if rel['target'] not in by_member:
                        raise ValueError('Embedded Word image missing from archive media')
                    asset = by_member[rel['target']]
                    images.append(asset)
                    return f"[Image: {asset['member']}]"
                if tag in {'footnoteReference', 'endnoteReference', 'commentReference'}:
                    warnings.add('Note/comment reference requires its original Word part; body extraction is not that note.')
                    return f"[{tag}: {node.get(f'{{{W}}}id', '?')}]"
                if tag == 'tbl':
                    number = table_indices[id(node)]
                    cells, text = [], []
                    for row_number, row in enumerate(node.findall(f'{{{W}}}tr'), 1):
                        for cell_number, cell in enumerate(row.findall(f'{{{W}}}tc'), 1):
                            props = cell.find(f'{{{W}}}tcPr')
                            span = props.find(f'{{{W}}}gridSpan') if props is not None else None
                            merge = props.find(f'{{{W}}}vMerge') if props is not None else None
                            value = ''.join(render(child) for child in cell).strip()
                            cell_info = {'row': row_number, 'cell': cell_number, 'text': value,
                                         'grid_span': span.get(f'{{{W}}}val') if span is not None else '1',
                                         'vertical_merge': merge.get(f'{{{W}}}val', 'continue') if merge is not None else None}
                            cells.append(cell_info)
                            text.append(f"[Table {number}, row {row_number}, cell {cell_number}, span {cell_info['grid_span']}, vertical merge {cell_info['vertical_merge'] or 'none'}]\n{value}")
                    tables.append({'table': number, 'cells': cells})
                    return '\n'.join(text) + '\n'
                value = ''.join(render(child) for child in node)
                if tag == 'r':
                    props = node.find(f'{{{W}}}rPr')
                    if value and (on(props, 'strike') or on(props, 'dstrike')):
                        value = '[crossed out: ' + value + ']'
                    if value and (on(props, 'vanish') or on(props, 'webHidden')):
                        value = '[hidden text: ' + value + ']'
                elif tag in {'del', 'moveFrom', 'ins', 'moveTo'} and value:
                    value = '[' + {'del': 'deleted', 'moveFrom': 'moved from', 'ins': 'inserted', 'moveTo': 'moved to'}[tag] + ': ' + value + ']'
                elif tag == 'hyperlink':
                    key = node.get(f'{{{R}}}id')
                    if key:
                        if key not in relationships:
                            raise ValueError('Word hyperlink relationship missing')
                        links.append({**relationships[key], 'label': value})
                elif tag == 'p':
                    props = node.find(f'{{{W}}}pPr')
                    numbering = props.find(f'{{{W}}}numPr') if props is not None else None
                    if numbering is not None:
                        identity = {local(n): n.get(f'{{{W}}}val') for n in numbering}
                        lists.append({'paragraph_zero_based': paragraph_indices[id(node)], **identity})
                        value = f"[List id {identity.get('numId', '?')}, level {identity.get('ilvl', '?')}; label not rendered] " + value
                        warnings.add('List identity/level retained; use converted page or original for visible numbering.')
                    value += '\n'
                return value

            text = render(block).strip()
            if not text:
                continue
            paragraph_ids = [paragraph_indices[id(p)] for p in block.iter(f'{{{W}}}p')]
            records.append({
                'schema_version': '1.0.0', 'source_id': source['source_id'], 'source_sha256': source['sha256'],
                'source_path': source['source_path'], 'format': 'docx', 'section': block_number,
                'locator': f"file:{source['source_id']}:s{block_number:04d}", 'search_text': text,
                'text_quality': 'native_word_body_supplement', 'ocr_status': 'not_used',
                'visual_dependency': bool(images or tables or lists or warnings),
                'visual_review_status': 'source_review_separate_from_extraction',
                'docx_native': {'part': part, 'part_sha256': part_hashes[part], 'body_block': block_number,
                                'kind': local(block), 'paragraphs_zero_based': paragraph_ids,
                                'tables': tables, 'lists': lists, 'links': links,
                                'images': list({image['path']: image for image in images}.values()),
                                'warnings': sorted(warnings)},
                'citation': {'source_id': source['source_id'], 'original_sha256': source['sha256'],
                             'section': block_number, 'part': part, 'body_block': block_number,
                             'location_basis': 'Word XML body block; not a printed or converted page number'},
            })
        # No writes until parsing and relationship checks have finished.
        asset_dir.mkdir(parents=True, exist_ok=True)
        for asset in assets:
            (root / asset['path']).write_bytes(archive.read(asset['member']))
        manifest = {'source_id': source['source_id'], 'source_sha256': source['sha256'],
                    'part_hashes': part_hashes, 'images': assets,
                    'paragraph_count_in_document_xml': len(paragraphs), 'table_count': len(table_indices),
                    'record_count': len(records), 'inherited_meaning_style_ids': style_meaning,
                    'scope': 'Main-body XML supplement; keep converted pages and original. Not a page renderer, list-number renderer or note/comment extractor.'}
        manifest_path = asset_dir / 'manifest.json'
        if not manifest_path.resolve().is_relative_to(root):
            raise ValueError('Word asset manifest escapes staging')
        encoded = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()
        manifest_path.write_bytes(encoded)
        return records, {'status': 'ok', 'native_record_count': len(records),
                         'native_asset_manifest': str(manifest_path.relative_to(root)),
                         'native_asset_manifest_sha256': sha(encoded), 'native_scope': manifest['scope']}
