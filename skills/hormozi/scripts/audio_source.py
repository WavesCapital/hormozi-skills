#!/usr/bin/env python3
"""Read saved original-audio transcripts with exact source and recheck lineage.

Read-only; no transcription, imports, source edits or doctrine promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

from corpus import contained_path


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def number(value) -> float:
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('Audio times must be finite nonnegative seconds.')
    return float(value)


def checked_json(root: Path, entry: dict) -> tuple[dict, Path]:
    path = contained_path(root, entry['path'])
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != entry['sha256']:
        raise ValueError('Saved audio evidence changed.')
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError('Audio evidence must be an object.')
    return data, path


def catalog(root: Path, expected: str | None = None) -> tuple[dict, dict]:
    path = contained_path(root, 'audio/catalog.json')
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if expected is not None and digest != expected:
        raise ValueError('Audio catalog changed; restart from checked metadata.')
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get('schema') != 'hormozi-original-audio/v1':
        raise ValueError('Unsupported audio catalog.')
    sources = data.get('sources')
    if not isinstance(sources, list) or not sources:
        raise ValueError('Audio source catalog is empty.')
    ids = [r['source_id'] for r in sources]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate original audio source identity.')
    return data, dict(catalog_path=str(path), catalog_sha256=digest)


def load(root: Path, source_id: str, source_root: Path, expected: str | None = None) -> dict:
    data, identity = catalog(root, expected)
    found = [r for r in data['sources'] if r['source_id'] == source_id]
    if len(found) != 1:
        raise ValueError('Exact original audio source not found.')
    source = found[0]
    # Check against the owning file manifest, not just the supplementary catalog.
    manifest = contained_path(root, 'files/file-source-manifest.jsonl')
    manifest_rows = [json.loads(line) for line in manifest.read_text().splitlines() if line.strip()]
    originals = [r for r in manifest_rows if r['source_id'] == source_id]
    if len(originals) != 1:
        raise ValueError('Original audio has no unique file manifest entry.')
    original_row = originals[0]
    advertised = original_row.get('audio_transcripts')
    if advertised is not None and advertised != {
            'catalog': 'audio/catalog.json', 'catalog_sha256': identity['catalog_sha256']}:
        raise ValueError('Owning file manifest pins another audio catalog.')
    if (original_row['sha256'] != source['source_sha256']
            or original_row['relative_path'] != source['relative_path']
            or original_row['extension'] not in ('.wav', '.mp4')):
        raise ValueError('Audio catalog and original manifest disagree.')
    original = contained_path(source_root, source['relative_path'])
    if sha(original) != source['source_sha256']:
        raise ValueError('Original audio changed.')
    review, review_path = checked_json(root, source['review'])
    if (review['source_id'] != source_id or review['source_sha256'] != source['source_sha256']
            or review['status'] != 'source_review_complete'):
        raise ValueError('Audio reading note identifies another or unfinished source.')
    versions, ids = [], set()
    for version in source['versions']:
        key = version['id']
        if key in ids or version['kind'] not in ('full', 'recheck'):
            raise ValueError('Invalid or duplicate audio version.')
        if (version['kind'] == 'full') != (key == 'full'):
            raise ValueError('The full transcript must use the full version ID.')
        ids.add(key)
        receipt, receipt_path = checked_json(root, version['receipt'])
        transcript, transcript_path = checked_json(root, version['transcript'])
        if (receipt['source_id'] != source_id or receipt['source_sha256'] != source['source_sha256']
                or receipt['original_unchanged'] is not True
                or receipt['status'] != 'transcribed_not_reviewed'
                or receipt['transcript_sha256'] != version['transcript']['sha256']):
            raise ValueError('Audio receipt identity or transcript hash differs.')
        streams = receipt['original_probe']['streams']
        if not streams or any(row['codec_type'] != 'audio' for row in streams):
            raise ValueError('This reader handles originals with audio streams only.')
        start = number(receipt['start_seconds'])
        duration = number(receipt['duration_seconds'])
        source_duration = number(receipt['source_duration_seconds'])
        if start + duration > source_duration + 0.01:
            raise ValueError('Audio version exceeds original duration.')
        segments = transcript['segments']
        if not segments or len(segments) != receipt['segment_count']:
            raise ValueError('Audio segment count differs from its receipt.')
        normalized, last_start = [], -1.0
        for index, segment in enumerate(segments):
            left, right = number(segment['start']), number(segment['end'])
            if left < last_start or right < left or right > duration + 0.1:
                raise ValueError('Audio segment times are invalid or out of order.')
            last_start = left
            if not isinstance(segment['text'], str):
                raise ValueError('Audio segment text must be a string.')
            normalized.append(dict(segment=index + 1, start_seconds=start + left,
                                   end_seconds=start + right, text=segment['text']))
        if version['kind'] == 'full':
            if start != 0 or duration != source_duration or review['transcript_sha256'] != version['transcript']['sha256']:
                raise ValueError('Full audio version is incomplete or differs from reviewed text.')
            interpretation = None
        else:
            matches = [r for r in review['audio_rechecks'] if r['receipt'] == version['audit_receipt']]
            if (len(matches) != 1 or matches[0]['transcript_sha256'] != version['transcript']['sha256']
                    or matches[0]['time_seconds'] != [start, start + duration]
                    or not matches[0].get('interpretation') or not matches[0].get('quality_note')):
                raise ValueError('Recheck lacks its exact reviewed interpretation.')
            interpretation = dict(interpretation=matches[0]['interpretation'], quality_note=matches[0]['quality_note'])
        versions.append(dict(id=key, kind=version['kind'], start_seconds=start,
                             end_seconds=start + duration, segments=normalized,
                             transcript_sha256=version['transcript']['sha256'],
                             transcript_path=str(transcript_path), receipt_path=str(receipt_path),
                             review=interpretation))
    if sum(v['kind'] == 'full' for v in versions) != 1:
        raise ValueError('Audio source needs exactly one full version.')
    if {v['audit_receipt'] for v in source['versions'] if v['kind'] == 'recheck'} != {
            r['receipt'] for r in review['audio_rechecks']}:
        raise ValueError('Not every reviewed recheck is retained.')
    return dict(**identity, source_id=source_id, title=source['title'],
                source_sha256=source['source_sha256'], original_path=str(original),
                review_path=str(review_path), source_review=review['source_review'], versions=versions)


def packet(source: dict, *, start: float = 0, end: float | None = None,
           query: str | None = None, version: str = 'full', offset: int = 0,
           expected: str | None = None, limit: int = 80, max_chars: int = 20000) -> dict:
    start = number(start)
    matches = [v for v in source['versions'] if v['id'] == version]
    if len(matches) != 1:
        raise ValueError('Exact audio version not found.')
    selected = matches[0]
    end = selected['end_seconds'] if end is None else number(end)
    if end < start or type(offset) is not int or offset < 0:
        raise ValueError('Invalid audio span or offset.')
    if (type(limit) is not int or type(max_chars) is not int
            or not 1 <= limit <= 200 or not 1 <= max_chars <= 40000):
        raise ValueError('Invalid packet limits.')
    terms = re.findall(r'\w+', query.casefold()) if query is not None else []
    if query is not None and not terms:
        raise ValueError('Search needs at least one word.')
    rows = [r for r in selected['segments'] if r['end_seconds'] >= start and r['start_seconds'] <= end
            and (query is None or all(term in r['text'].casefold() for term in terms))]
    basis = dict(catalog=source['catalog_sha256'], source=source['source_id'],
                 transcript=selected['transcript_sha256'], version=version, start=start, end=end, query=query)
    content_hash = hashlib.sha256(json.dumps(basis, sort_keys=True).encode()).hexdigest()
    if (expected is not None and expected != content_hash) or (offset and expected is None):
        raise ValueError('Follow-up packets need the matching content hash.')
    if offset > len(rows):
        raise ValueError('Audio offset exceeds the selected results.')
    page, size = [], 0
    for row in rows[offset:offset + limit]:
        if size + len(row['text']) > max_chars:
            if not page:
                raise ValueError('One segment exceeds the packet budget; increase max-chars.')
            break
        page.append(row)
        size += len(row['text'])
    next_offset = offset + len(page)
    rechecks = [dict(id=v['id'], start_seconds=v['start_seconds'], end_seconds=v['end_seconds'],
                    transcript_sha256=v['transcript_sha256'], **v['review'])
                for v in source['versions'] if v['kind'] == 'recheck'
                and v['end_seconds'] >= start and v['start_seconds'] <= end]
    return {k: source[k] for k in ('source_id', 'title', 'source_sha256', 'original_path',
                                   'catalog_sha256', 'review_path')} | dict(
        version=version, transcript_sha256=selected['transcript_sha256'],
        transcript_path=selected['transcript_path'], content_sha256=content_hash,
        selected_segments=len(rows), offset=offset, segments=page,
        next_offset=next_offset if next_offset < len(rows) else None,
        related_rechecks=rechecks,
        evidence_limit='Machine transcript and saved review, not a verbatim authenticated quote or a fresh audio listen. Rechecks are separate versions, not silent corrections. Times are seconds in the original file; cite its title and exact span.')


def verify(root: Path, source_root: Path) -> dict:
    """Check every advertised original-audio source and evidence file, without text output."""
    manifest = [json.loads(line) for line in contained_path(root, 'files/file-source-manifest.jsonl').read_text().splitlines() if line.strip()]
    originals = [r for r in manifest if r.get('extension') in ('.wav', '.mp4') and r.get('category') == 'media-only']
    if not originals and not (root / 'audio/catalog.json').exists():
        return dict(sources=0, versions=0, segments=0, evidence_files=0)
    data, identity = catalog(root)
    if {r['source_id'] for r in originals} != {r['source_id'] for r in data['sources']}:
        raise ValueError('Original audio catalog coverage differs from the file manifest.')
    for row in originals:
        if (row.get('audio_transcripts') != {'catalog': 'audio/catalog.json', 'catalog_sha256': identity['catalog_sha256']}
                or row['processing']['status'] != 'audio_transcripts_available'):
            raise ValueError('Owning file manifest does not pin the audio catalog.')
    expected = {'audio/catalog.json'}
    versions = segments = 0
    for row in data['sources']:
        expected.add(row['review']['path'])
        for version in row['versions']:
            expected.update((version['receipt']['path'], version['transcript']['path']))
        checked = load(root, row['source_id'], source_root, identity['catalog_sha256'])
        versions += len(checked['versions'])
        segments += sum(len(v['segments']) for v in checked['versions'])
    actual = {str(p.relative_to(root)) for p in (root / 'audio').rglob('*') if p.is_file()}
    if actual != expected:
        raise ValueError('Audio evidence files are missing or unaccounted.')
    return dict(sources=len(originals), versions=versions, segments=segments,
                evidence_files=len(expected), catalog_sha256=identity['catalog_sha256'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('list', 'read', 'search', 'verify'))
    parser.add_argument('--corpus-root', type=Path, required=True)
    parser.add_argument('--source-root', type=Path)
    parser.add_argument('--source-id')
    parser.add_argument('--expected-catalog-sha256')
    parser.add_argument('--version', default='full')
    parser.add_argument('--start-seconds', type=float, default=0)
    parser.add_argument('--end-seconds', type=float)
    parser.add_argument('--query')
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--expected-content-sha256')
    parser.add_argument('--limit', type=int, default=80)
    parser.add_argument('--max-chars', type=int, default=20000)
    args = parser.parse_args()
    try:
        if args.action == 'list':
            data, identity = catalog(args.corpus_root, args.expected_catalog_sha256)
            result = dict(**identity, sources=[{k: s[k] for k in ('source_id', 'title', 'source_sha256')}
                                              for s in data['sources']])
        elif args.action == 'verify':
            if args.source_root is None:
                raise ValueError('Verification requires the original-source root.')
            result = verify(args.corpus_root, args.source_root)
        else:
            if args.source_root is None or not args.source_id:
                raise ValueError('Reading requires the exact source ID and original-source root.')
            if args.action == 'search' and args.query is None:
                raise ValueError('Search requires --query.')
            source = load(args.corpus_root, args.source_id, args.source_root, args.expected_catalog_sha256)
            result = packet(source, start=args.start_seconds, end=args.end_seconds,
                            query=args.query if args.action == 'search' else None,
                            version=args.version, offset=args.offset, expected=args.expected_content_sha256,
                            limit=args.limit, max_chars=args.max_chars)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(2, f'Audio source unavailable: {error}\n')


if __name__ == '__main__':
    main()
