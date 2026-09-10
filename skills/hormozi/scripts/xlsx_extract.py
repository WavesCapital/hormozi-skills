"""Read native XLSX evidence without changing or recalculating the workbook.

Rows supplement converted pages. Formulas and cached values are distinct;
styles, notes, drawings and original media remain linked to sheet identities.
This is not a renderer. The caller owns staging, validation and promotion.
"""
from __future__ import annotations

import hashlib
import io
import json
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

S = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
DATE_FORMATS = {14: 'mm-dd-yy', 15: 'd-mmm-yy', 16: 'd-mmm', 17: 'mmm-yy', 22: 'm/d/yy h:mm'}


def calendar_value(raw: str | None, number_format: str | None, date1904: bool) -> tuple[str | None, str | None]:
    """Decode recognizable date formats, not arbitrary Excel display syntax."""
    if raw is None or not number_format:
        return None, None
    code = re.sub(r'"[^\"]*"|\\.|\[[^\]]*\]', '', number_format).split(';')[0]
    if not re.search('[yd]', code, re.I):
        return None, None
    try:
        serial = Decimal(raw)
        if not serial.is_finite() or serial < 0 or serial > 2958465:
            return None, 'Date serial outside supported nonnegative calendar range; inspect original.'
        if not date1904 and 60 <= serial < 61:
            return None, 'Excel 1900-system serial 60 is a fictitious leap date; no real date inferred.'
        epoch = datetime(1904, 1, 1) if date1904 else datetime(1899, 12, 30)
        if not date1904 and serial < 60:
            serial += 1
        microseconds = int((serial * 86400000000).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))
        return (epoch + timedelta(microseconds=microseconds)).isoformat(sep=' '), None
    except (InvalidOperation, OverflowError, ValueError):
        return None, 'Date serial could not be decoded; inspect original.'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def xml(data: bytes) -> ET.Element:
    if b'\x00' in data or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('Unsupported workbook XML encoding or declaration')
    return ET.fromstring(data.decode('utf-8-sig'))


def member(base: str, target: str) -> str:
    parts = urlsplit(target)
    path = unquote(parts.path)
    if parts.scheme or parts.netloc or parts.query or parts.fragment or '\\' in path or '\x00' in path:
        raise ValueError('Workbook relationship must be an archive member')
    # OPC permits package-absolute part names, but never filesystem paths.
    resolved = posixpath.normpath(path.lstrip('/') if path.startswith('/') else
                                 posixpath.join(posixpath.dirname(base), path))
    if resolved in {'', '.', '..'} or resolved.startswith('../'):
        raise ValueError('Workbook relationship escapes archive')
    return resolved


def tree(node: ET.Element) -> dict:
    """Preserve namespaced native metadata, including child order and text."""
    return {'tag': node.tag, 'attributes': dict(node.attrib), 'text': node.text,
            'children': [tree(child) for child in node]}


def rich_text(node: ET.Element) -> dict:
    # Phonetic guides are retained in XML metadata, not inserted into prose.
    runs = []
    for child in node:
        if child.tag == f'{{{S}}}t':
            runs.append({'text': child.text or '', 'properties': None})
        elif child.tag == f'{{{S}}}r':
            props = child.find(f'{{{S}}}rPr')
            runs.append({'text': ''.join(n.text or '' for n in child.findall(f'{{{S}}}t')),
                         'properties': tree(props) if props is not None else None})
    marked = []
    for run in runs:
        strike = next((p for p in (run['properties'] or {}).get('children', [])
                       if p['tag'] == f'{{{S}}}strike'), None)
        struck = strike is not None and strike['attributes'].get('val', '1').lower() not in {'0', 'false', 'off'}
        marked.append('[crossed out: ' + run['text'] + ']' if struck else run['text'])
    return {'text': ''.join(run['text'] for run in runs), 'marked_text': ''.join(marked),
            'runs': runs, 'xml': tree(node)}


def extract(source: dict, original: Path) -> tuple[list[dict], dict, dict[str, bytes]]:
    """Return evidence and media bytes; perform no writes or network access."""
    raw = original.read_bytes()
    if sha(raw) != source['sha256']:
        raise ValueError('Workbook original hash mismatch')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or len(names) > 20000 or sum(i.file_size for i in archive.infolist()) > 256 * 1024 * 1024:
            raise ValueError('Duplicate or oversized workbook archive')
        part_hashes = {}

        def read(part):
            content = archive.read(part)
            part_hashes[part] = sha(content)
            return xml(content)

        def relationships(part):
            path = posixpath.join(posixpath.dirname(part), '_rels', posixpath.basename(part) + '.rels')
            result = {}
            if path in names:
                for rel in read(path):
                    key, target = rel.get('Id'), rel.get('Target')
                    if not key or key in result or not target:
                        raise ValueError('Missing or duplicate workbook relationship identity')
                    external = rel.get('TargetMode') == 'External'
                    result[key] = {'id': key, 'type': rel.get('Type', ''), 'external': external,
                                   'target': target if external else member(part, target)}
            return result

        root_rels = relationships('')
        roots = [r for r in root_rels.values() if r['type'].endswith('/officeDocument')]
        if len(roots) != 1 or roots[0]['external']:
            raise ValueError('Workbook must have one local office document')
        workbook_part = roots[0]['target']
        workbook = read(workbook_part)
        if workbook.tag != f'{{{S}}}workbook':
            raise ValueError('Unsupported workbook namespace')
        book_rels = relationships(workbook_part)
        shared, styles, themes = [], None, []
        for rel in book_rels.values():
            if rel['type'].endswith(('/sharedStrings', '/styles')):
                if rel['external']:
                    raise ValueError('Workbook strings/styles cannot be external')
                node = read(rel['target'])
                if rel['type'].endswith('/sharedStrings'):
                    shared = [rich_text(n) for n in node.findall(f'{{{S}}}si')]
                else:
                    styles = tree(node)
            elif rel['type'].endswith('/theme'):
                if rel['external']:
                    raise ValueError('Workbook theme cannot be external')
                themes.append({'part': rel['target'], 'xml': tree(read(rel['target']))})
        cells_styles = next((n['children'] for n in (styles or {}).get('children', [])
                             if n['tag'] == f'{{{S}}}cellXfs'), [])
        number_formats = {**DATE_FORMATS}
        for group in (styles or {}).get('children', []):
            if group['tag'] == f'{{{S}}}numFmts':
                number_formats.update({int(n['attributes']['numFmtId']): n['attributes']['formatCode'] for n in group['children']})
        workbook_props = workbook.find(f'{{{S}}}workbookPr')
        date1904 = workbook_props is not None and workbook_props.get('date1904', '0').lower() in {'1', 'true'}
        media_bytes, media = {}, []
        for name in names:
            if not name.startswith('xl/media/') or name.endswith('/'):
                continue
            data = archive.read(name)
            suffix = Path(name).suffix.lower()
            if not re.fullmatch(r'\.[a-z0-9]{1,8}', suffix):
                suffix = '.bin'
            key = sha(data) + suffix
            media_bytes[key] = data
            media.append({'member': name, 'asset_name': key, 'sha256': sha(data), 'byte_size': len(data)})
        by_member = {m['member']: m for m in media}
        records, sheets = [], []
        seen_sheet_names, seen_sheet_ids = set(), set()
        for sheet_order, sheet in enumerate(workbook.findall(f'{{{S}}}sheets/{{{S}}}sheet'), 1):
            name, identity = sheet.get('name'), sheet.get('sheetId')
            if not name or not identity or name in seen_sheet_names or identity in seen_sheet_ids:
                raise ValueError('Missing or duplicate workbook sheet identity')
            seen_sheet_names.add(name)
            seen_sheet_ids.add(identity)
            rel = book_rels.get(sheet.get(f'{{{R}}}id'))
            if not rel or rel['external'] or not rel['type'].endswith('/worksheet'):
                raise ValueError('Unsupported or missing worksheet relationship')
            part = rel['target']
            sheet_xml = read(part)
            if sheet_xml.tag != f'{{{S}}}worksheet':
                raise ValueError('Unsupported worksheet namespace')
            rels = relationships(part)
            notes, drawings = {}, []
            for related in rels.values():
                if related['type'].endswith('/comments'):
                    if related['external']:
                        raise ValueError('Workbook cell notes cannot be external')
                    note_root = read(related['target'])
                    authors = [a.text or '' for a in note_root.findall(f'{{{S}}}authors/{{{S}}}author')]
                    for note in note_root.findall(f'{{{S}}}commentList/{{{S}}}comment'):
                        cell = note.attrib['ref']
                        if cell in notes:
                            raise ValueError('Duplicate workbook cell note')
                        author = int(note.attrib['authorId'])
                        if author < 0 or author >= len(authors):
                            raise ValueError('Invalid workbook note author')
                        body = note.find(f'{{{S}}}text')
                        notes[cell] = {'author': authors[author], **rich_text(body)} if body is not None else {'author': authors[author], 'text': ''}
                elif related['type'].endswith('/drawing'):
                    if related['external']:
                        raise ValueError('Workbook drawing cannot be external')
                    drawing_part = related['target']
                    drawing_xml, drawing_rels = read(drawing_part), relationships(drawing_part)
                    images = []
                    for image_rel in drawing_rels.values():
                        if image_rel['type'].endswith('/image') and not image_rel['external']:
                            if image_rel['target'] not in by_member:
                                raise ValueError('Workbook embedded image is missing')
                            images.append(by_member[image_rel['target']])
                    drawings.append({'part': drawing_part, 'xml': tree(drawing_xml),
                                     'relationships': drawing_rels, 'images': images})
            links = []
            for link in sheet_xml.findall(f'{{{S}}}hyperlinks/{{{S}}}hyperlink'):
                key = link.get(f'{{{R}}}id')
                if key and key not in rels:
                    raise ValueError('Workbook hyperlink relationship is missing')
                links.append({'attributes': dict(link.attrib), 'relationship': rels.get(key)})
            metadata = {'sheet_name': name, 'sheet_id': identity, 'sheet_order': sheet_order,
                        'part': part, 'part_sha256': part_hashes[part], 'state': sheet.get('state', 'visible'),
                        'structure': [tree(n) for n in sheet_xml if n.tag != f'{{{S}}}sheetData'],
                        'relationships': rels, 'notes': notes, 'hyperlinks': links, 'drawings': drawings,
                        'row_attributes': [], 'style_only_cells': [], 'content_cell_count': 0}
            sheets.append(metadata)

            def add(text, native, citation):
                number = len(records) + 1
                records.append({'schema_version': '1.0.0', 'source_id': source['source_id'],
                                'source_sha256': source['sha256'], 'source_path': source['source_path'],
                                'format': 'xlsx', 'section': number,
                                'locator': f"file:{source['source_id']}:s{number:04d}",
                                'search_text': text, 'text_quality': 'native_workbook_supplement',
                                'ocr_status': 'not_used', 'visual_dependency': True,
                                'visual_review_status': 'source_review_separate_from_extraction',
                                'xlsx_native': {'sheet_name': name, 'sheet_id': identity,
                                                'sheet_order': sheet_order, 'part': part,
                                                'part_sha256': part_hashes[part], **native},
                                'citation': {'source_id': source['source_id'], 'original_sha256': source['sha256'],
                                             'section': number, 'sheet_name': name, 'sheet_id': identity,
                                             'location_basis': 'Native worksheet cells; not a converted PDF page', **citation}})

            add(f"Worksheet: {name}\nSheet state: {metadata['state']}\nEmbedded drawings: {len(drawings)}\nRead native rows with their headers and any color key; colors alone do not prove approval or sending.",
                {'kind': 'sheet', 'drawings': drawings}, {})
            seen_cells, seen_rows = set(), set()
            for row in sheet_xml.findall(f'{{{S}}}sheetData/{{{S}}}row'):
                row_number = int(row.attrib['r'])
                if row_number in seen_rows or not 1 <= row_number <= 1048576:
                    raise ValueError('Duplicate or invalid workbook row')
                seen_rows.add(row_number)
                metadata['row_attributes'].append(dict(row.attrib))
                values, text = [], []
                for cell in row.findall(f'{{{S}}}c'):
                    address = cell.attrib['r']
                    match = re.fullmatch(r'([A-Z]{1,3})([1-9][0-9]*)', address)
                    if not match or int(match[2]) != row_number or address in seen_cells:
                        raise ValueError('Duplicate or invalid workbook cell address')
                    column = 0
                    for letter in match[1]:
                        column = column * 26 + ord(letter) - ord('A') + 1
                    if column > 16384:
                        raise ValueError('Workbook cell column is out of bounds')
                    seen_cells.add(address)
                    style = int(cell.get('s', '0'))
                    if style < 0 or (style >= len(cells_styles) and (cells_styles or style != 0)):
                        raise ValueError('Workbook cell style index is invalid')
                    kind = cell.get('t', 'n')
                    value, formula, inline = cell.find(f'{{{S}}}v'), cell.find(f'{{{S}}}f'), cell.find(f'{{{S}}}is')
                    raw_value = value.text if value is not None else None
                    rich = None
                    if kind == 's' and raw_value is not None:
                        index = int(raw_value)
                        if index < 0 or index >= len(shared):
                            raise ValueError('Workbook shared string index is invalid')
                        rich = shared[index]
                    elif inline is not None:
                        rich = rich_text(inline)
                    display = rich['text'] if rich is not None else (raw_value or '')
                    format_id = int(cells_styles[style]['attributes'].get('numFmtId', '0')) if cells_styles else 0
                    number_format = number_formats.get(format_id)
                    date_value, date_warning = calendar_value(raw_value, number_format, date1904) if kind == 'n' else (None, None)
                    if date_value is not None:
                        display = date_value
                    item = {'address': address, 'attributes': dict(cell.attrib), 'data_type': kind,
                            'raw_value': raw_value, 'text': display, 'rich_text': rich,
                            'number_format_id': format_id, 'number_format': number_format,
                            'calendar_value': date_value, 'date_warning': date_warning,
                            'style_index': style, 'formula': tree(formula) if formula is not None else None,
                            'note': notes.get(address)}
                    values.append(item)
                    if display or formula is not None or address in notes:
                        metadata['content_cell_count'] += 1
                        line = f"{address}: {rich['marked_text'] if rich is not None else display}"
                        if formula is not None:
                            line += f' [Formula: {formula.text or ""}; cached value only, not recalculated]'
                        if date_warning:
                            line += f' [{date_warning}]'
                        if address in notes:
                            line += f" [Cell note: {notes[address]['text']}]"
                        text.append(line)
                    else:
                        metadata['style_only_cells'].append({'address': address, 'attributes': dict(cell.attrib)})
                if text:
                    add(f'Worksheet: {name}; row {row_number}\n' + '\n'.join(text),
                        {'kind': 'row', 'row': row_number, 'cells': values}, {'row': row_number})
            orphan_notes = set(notes) - seen_cells
            if orphan_notes:
                # Notes need not have a corresponding <c>; retain and expose them.
                for address in sorted(orphan_notes):
                    add(f"Worksheet: {name}; note at {address}\n{notes[address]['text']}",
                        {'kind': 'note', 'cell': address, 'note': notes[address]}, {'cell': address})
        if not sheets:
            raise ValueError('Workbook has no worksheets')
        catalog = {'source_id': source['source_id'], 'source_sha256': source['sha256'],
                   'workbook_part': workbook_part, 'workbook_structure': tree(workbook),
                   'relationships': book_rels, 'part_hashes': part_hashes, 'styles': styles, 'themes': themes,
                   'sheets': sheets, 'images': media, 'record_count': len(records),
                   'scope': 'Native cell and metadata supplement. Keep converted pages and original. Recognizable dates decode using the workbook epoch; raw serials remain intact. No formula recalculation, full Excel number-format rendering, effective-style rendering or drawing interpretation. Formula results are saved caches only. External links are not fetched.'}
        return records, catalog, media_bytes


def records_digest(records: list[dict]) -> str:
    return sha(json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())


def stage(source: dict, original: Path, derived_root: Path) -> tuple[list[dict], dict]:
    """Write an already parsed supplement only to the caller's staging root."""
    records, catalog, assets = extract(source, original)
    root = derived_root.resolve()
    slug = re.sub(r'[^a-zA-Z0-9_-]', '-', source['source_id'])
    folder = root / 'xlsx-assets' / slug
    if not folder.resolve().is_relative_to(root):
        raise ValueError('Workbook asset directory escapes staging')
    for asset in catalog['images']:
        destination = folder / asset['asset_name']
        if not destination.resolve().is_relative_to(root):
            raise ValueError('Workbook image path escapes staging')
        asset['path'] = str(destination.relative_to(root))
    # Drawings and catalog images share the same asset records from extraction.
    # Bind all native text and metadata to the catalog, not just its row count.
    catalog['native_records_digest'] = records_digest(records)
    path = folder / 'manifest.json'
    if not path.resolve().is_relative_to(root):
        raise ValueError('Workbook catalog path escapes staging')
    encoded = (json.dumps(catalog, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    folder.mkdir(parents=True, exist_ok=True)
    for asset in catalog['images']:
        (root / asset['path']).write_bytes(assets[asset['asset_name']])
    path.write_bytes(encoded)
    return records, {'native_record_count': len(records), 'native_asset_manifest': str(path.relative_to(root)),
                     'native_asset_manifest_sha256': sha(encoded), 'native_scope': catalog['scope']}
