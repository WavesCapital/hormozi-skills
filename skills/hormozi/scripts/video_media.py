"""Read source-local video images and ASR rechecks after video_source's scope gate.

No import, media capture, source edits, or review credit. Catalogs identify saved
evidence; they do not turn captions, ASR, and images into interchangeable proof.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


HASH = re.compile(r"[a-f0-9]{64}")


def file_hash(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def checked_path(root: Path, relative: str) -> Path:
    if (not isinstance(relative, str) or not relative or '\\' in relative
            or PurePosixPath(relative).is_absolute()
            or any(part in {'.', '..', ''} for part in relative.split('/'))):
        raise ValueError('Invalid media path.')
    root = root.resolve(strict=True)
    target = root / relative
    if target.resolve(strict=True) != target:
        raise ValueError('Media path must not redirect through a symlink.')
    if not target.is_file():
        raise ValueError('Media asset is not a file.')
    return target


def asset(root: Path, ref: dict) -> Path:
    if not isinstance(ref, dict) or not HASH.fullmatch(str(ref.get('sha256', ''))):
        raise ValueError('Media asset needs a valid saved hash.')
    path = checked_path(root, ref.get('path'))
    if file_hash(path) != ref['sha256']:
        raise ValueError('Media asset hash mismatch: ' + ref['path'])
    return path


def seconds_ms(value) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError('Media time needs nonnegative seconds.')
    try:
        number = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError('Invalid media seconds.') from error
    if not number.is_finite() or number < 0:
        raise ValueError('Media time needs finite, nonnegative seconds.')
    # ASR emits binary float artifacts such as 11.600000000000001. Returned
    # milliseconds are rounded; preserve original seconds beside each record.
    return int((number * 1000).to_integral_value(rounding=ROUND_HALF_UP))


def read_json(path: Path) -> dict:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError('Media record must be an object.')
    return value


def load(root: Path, row: dict, raw_hash: str, expected: str | None):
    """Only call after metadata eligibility and exact raw-transcript checks."""
    library = root.resolve() / 'youtube/media'
    if library.resolve(strict=True) != library:
        raise ValueError('Media library must not redirect through a symlink.')
    pointer = read_json(checked_path(library, 'catalog.json'))
    if pointer.get('schema') != 'hormozi-video-media-index/v1':
        raise ValueError('Unknown video media index schema.')
    sources = pointer.get('sources')
    if not isinstance(sources, list) or any(not isinstance(s, dict) for s in sources):
        raise ValueError('Invalid video media source index.')
    ids = [s.get('video_id') for s in sources]
    if any(not isinstance(i, str) or not re.fullmatch(r'[A-Za-z0-9_-]{11}', i) for i in ids) or len(ids) != len(set(ids)):
        raise ValueError('Invalid or duplicate media video identity.')
    matches = [s for s in sources if s['video_id'] == row['video_id']]
    if len(matches) != 1:
        raise ValueError('No saved media for this video.')
    ref = matches[0].get('catalog')
    if not isinstance(ref, dict) or ref.get('path') != f"sources/{row['video_id']}/catalog.json":
        raise ValueError('Media catalog path does not match video identity.')
    if expected is not None and ref.get('sha256') != expected:
        raise ValueError('Media catalog changed; repeat discovery before reading.')
    path = asset(library, ref)
    data = read_json(path)
    if data.get('schema') != 'hormozi-video-media/v1':
        raise ValueError('Unknown video media schema.')
    from video_source import timestamp
    identity = data.get('source', {})
    for key in ('video_id', 'channel_id', 'channel_identity_verified', 'content_type'):
        if identity.get(key) != row.get(key):
            raise ValueError('Media source identity differs from selected video.')
    if timestamp(identity.get('publication_time')) != timestamp(row.get('publication_time')):
        raise ValueError('Media publication time differs from selected video.')
    variants = data.get('frozen_variants')
    if not isinstance(variants, list) or not variants:
        raise ValueError('Media has no frozen caption lineage.')
    hashes = [v.get('content_sha256') for v in variants]
    if len(hashes) != len(set(hashes)) or any(not HASH.fullmatch(str(h)) for h in hashes):
        raise ValueError('Invalid frozen caption identity.')
    if any(not isinstance(v.get('raw_sha256'), list) or not v['raw_sha256']
           or any(not HASH.fullmatch(str(h)) for h in v['raw_sha256']) for v in variants):
        raise ValueError('Invalid frozen raw caption hashes.')
    if sum(raw_hash in v['raw_sha256'] for v in variants) != 1:
        raise ValueError('Selected captions were not part of this saved media review.')
    local = path.parent
    capture = read_json(asset(local, data.get('capture_manifest')))
    if capture.get('video_id') != row['video_id'] or set(capture.get('frozen_transcript_hashes', [])) != set(hashes):
        raise ValueError('Capture manifest has different video or captions.')
    timestamp(capture.get('captured_at'))
    media_ref = data.get('media')
    if not isinstance(media_ref, dict) or capture.get('media_sha256') != media_ref.get('sha256'):
        raise ValueError('Capture and preserved media disagree.')
    media_path = asset(local, media_ref)
    return data, capture, local, {'catalog_path': str(path), 'catalog_sha256': ref['sha256'],
        'media_path': str(media_path), 'media_sha256': media_ref['sha256'],
        'captured_at': capture['captured_at'], 'frozen_variants': variants}


def recheck_meta(local: Path, data: dict, capture: dict) -> list[dict]:
    entries = data.get('rechecks')
    if not isinstance(entries, list):
        raise ValueError('Media rechecks must be a list.')
    result, seen = [], set()
    for item in entries:
        key = item.get('id')
        if not isinstance(key, str) or not re.fullmatch(r'[a-zA-Z0-9_-]+', key) or key in seen:
            raise ValueError('Invalid or duplicate recheck ID.')
        seen.add(key)
        receipt = read_json(asset(local, item.get('receipt')))
        if (receipt.get('video_id') != data['source']['video_id']
                or set(receipt.get('frozen_transcript_variants', [])) != set(capture['frozen_transcript_hashes'])):
            raise ValueError('Recheck belongs to another media source or caption version.')
        media_ref = item.get('media')
        if not isinstance(media_ref, dict) or media_ref.get('sha256') != receipt.get('media_sha256'):
            raise ValueError('Recheck belongs to another media capture than its saved asset.')
        # Some checks use a separate audio-only download of the same video.
        # Preserve that capture; never substitute the frame video's byte hash.
        media_path = asset(local, media_ref) if media_ref != data['media'] else local / media_ref['path']
        start = seconds_ms(receipt.get('start_seconds'))
        duration = seconds_ms(receipt.get('duration_seconds'))
        if duration <= 0:
            raise ValueError('Recheck duration must be positive.')
        transcript = item.get('transcript')
        if not isinstance(transcript, dict) or receipt.get('transcript_sha256') != transcript.get('sha256'):
            raise ValueError('Recheck transcript and receipt disagree.')
        result.append({'id': key, 'start_ms': start, 'end_ms': start + duration,
                       'source_start_seconds': receipt['start_seconds'],
                       'receipt_status': receipt.get('status'),
                       'media_path': str(media_path), 'media_sha256': media_ref['sha256'],
                       'same_capture_as_frames': media_ref['sha256'] == capture['media_sha256'],
                       'receipt': item['receipt'], 'transcript': transcript})
    return result


def packet(args, row: dict, raw_hash: str) -> dict:
    from video_source import digest, page_records
    if args.start_ms < 0 or args.end_ms <= args.start_ms:
        raise ValueError('Media read needs an increasing nonnegative millisecond range.')
    data, capture, local, lineage = load(Path(args.corpus_root), row, raw_hash, args.expected_catalog_sha256)
    rechecks = recheck_meta(local, data, capture)
    signature = digest(json.dumps([lineage, args.action, args.start_ms, args.end_ms,
                                   args.recheck_id, args.media_kind], sort_keys=True).encode())
    if args.offset and not args.expected_content_sha256:
        raise ValueError('Continued media reads require --expected-content-sha256.')
    if args.expected_content_sha256 is not None and args.expected_content_sha256 != signature:
        raise ValueError('Media packet changed between reads.')
    related = [r for r in rechecks if r['end_ms'] >= args.start_ms and r['start_ms'] <= args.end_ms]
    common = {**lineage, 'schema': 'scoped_video_media_v1', 'content_sha256': signature,
              'requested_start_ms': args.start_ms, 'requested_end_ms': args.end_ms,
              'review_limits': 'Saved images and separate machine audio passes. Hashes are not image viewing, fresh listening, frozen video-byte identity, or doctrine approval.',
              'related_rechecks': [{k: v for k, v in r.items() if k not in {'receipt', 'transcript'}} for r in related]}
    if args.action == 'media':
        items = capture.get(args.media_kind)
        if not isinstance(items, list) or not items:
            raise ValueError('Capture has no images of this kind.')
        names, records = set(), []
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get('path'), str) or item['path'] in names:
                raise ValueError('Invalid or duplicate capture image.')
            names.add(item['path'])
            time = seconds_ms(item.get('seconds')) if args.media_kind == 'frames' else None
            if time is not None and not args.start_ms <= time <= args.end_ms:
                continue
            records.append({**item, 'start_ms': time})
        records.sort(key=lambda r: (r['start_ms'] if r['start_ms'] is not None else 0, r['path']))
        if args.offset > len(records) or (args.offset and args.offset == len(records)):
            raise ValueError('Offset is beyond media results.')
        result = []
        for item in records[args.offset:args.offset + args.limit]:
            p = asset(local, item)
            result.append({**item, 'path': str(p), 'image_viewed_now': False})
        common['content_scope'] = ('frames_in_requested_range' if args.media_kind == 'frames'
                                   else 'contact_sheets_for_whole_video_not_time_filtered')
    else:
        matches = [r for r in rechecks if r['id'] == args.recheck_id]
        if len(matches) != 1:
            raise ValueError('Unknown recheck ID; discover it with media first.')
        entry = matches[0]
        transcript = read_json(asset(local, entry['transcript']))
        segments = transcript.get('segments')
        if not isinstance(segments, list) or not segments:
            raise ValueError('Recheck transcript is empty.')
        records, last = [], -1
        for number, segment in enumerate(segments, 1):
            if not isinstance(segment, dict) or not isinstance(segment.get('text'), str):
                raise ValueError('Recheck segment needs text.')
            start, end = seconds_ms(segment.get('start')), seconds_ms(segment.get('end'))
            if end < start or start < last or end > entry['end_ms'] - entry['start_ms']:
                raise ValueError('Recheck times are reversed, unordered, or outside its span.')
            last = start
            start, end = start + entry['start_ms'], end + entry['start_ms']
            if end >= args.start_ms and start <= args.end_ms:
                seconds = start // 1000
                records.append({'segment': number, 'start_ms': start, 'end_ms': end,
                    'source_local_start_seconds': segment['start'], 'source_local_end_seconds': segment['end'],
                    'source_clip_start_seconds': entry['source_start_seconds'],
                    'text': segment['text'], 'time_link': f"[{seconds//60:02d}:{seconds%60:02d}](https://www.youtube.com/watch?v={row['video_id']}&t={seconds}s)"})
        if not records or args.offset >= len(records):
            raise ValueError('No recheck segments at this range or offset.')
        result = page_records(records, args.offset, args.limit)
        common |= {'content_scope': 'machine_recheck_not_original_captions_or_fresh_listening',
                   'recheck_id': entry['id'], 'receipt_path': str(asset(local, entry['receipt'])),
                   'recheck_media_path': entry['media_path'], 'recheck_media_sha256': entry['media_sha256'],
                   'transcript_path': str(asset(local, entry['transcript']))}
    end = args.offset + len(result)
    return {**common, 'records': result, 'total_records': len(records), 'offset': args.offset,
            'next_offset': end if end < len(records) else None,
            'packet_complete': args.offset == 0 and end == len(records)}
