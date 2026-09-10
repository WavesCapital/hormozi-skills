"""Synthetic original-audio lineage and bounded-read tests; no reading credit."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/hormozi/scripts'))
import audio_source as reader


class AudioSourceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.originals = self.root / 'originals'
        self.originals.mkdir()
        (self.originals / 'source.wav').write_bytes(b'fictional original')
        self.digest = reader.sha(self.originals / 'source.wav')
        self.corpus = self.root / 'corpus'
        (self.corpus / 'files').mkdir(parents=True)
        (self.corpus / 'files/file-source-manifest.jsonl').write_text(json.dumps(dict(
            source_id='audio', relative_path='source.wav', sha256=self.digest, extension='.wav')) + '\n')
        self.review = dict(source_id='audio', source_sha256=self.digest, status='source_review_complete',
                           source_review={'attribution': 'Fictional test'}, audio_rechecks=[])
        versions = []
        for kind, start, duration in [('full', 0, 20), ('recheck', 10, 5)]:
            name = 'full' if kind == 'full' else 'recheck-01'
            segments = [dict(start=0, end=2, text='Keep the price clear.'),
                        dict(start=2, end=4, text='Do not merge versions.')]
            transcript = self.write(f'audio/{name}-transcript.json', {'segments': segments})
            receipt = dict(source_id='audio', source_sha256=self.digest, original_unchanged=True,
                           status='transcribed_not_reviewed', transcript_sha256=transcript['sha256'],
                           original_probe={'streams': [{'codec_type': 'audio'}]}, start_seconds=start,
                           duration_seconds=duration, source_duration_seconds=20, segment_count=2)
            versions.append(dict(id=name, kind=kind, audit_receipt=f'audit/{name}',
                                 receipt=self.write(f'audio/{name}-receipt.json', receipt), transcript=transcript))
            if kind == 'full':
                self.review['transcript_sha256'] = transcript['sha256']
            else:
                self.review['audio_rechecks'].append(dict(receipt=f'audit/{name}',
                    transcript_sha256=transcript['sha256'], time_seconds=[10, 15],
                    interpretation='A separate check, not a correction.', quality_note='Synthetic.'))
        self.source = dict(source_id='audio', source_sha256=self.digest, relative_path='source.wav',
                           title='Fictional audio', review=self.write('audio/review.json', self.review), versions=versions)
        self.save_catalog()

    def write(self, relative, data):
        path = self.corpus / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
        return dict(path=relative, sha256=reader.sha(path))

    def save_catalog(self):
        self.write('audio/catalog.json', dict(schema='hormozi-original-audio/v1', sources=[self.source]))

    def load(self):
        return reader.load(self.corpus, 'audio', self.originals)

    def advertise(self):
        path = self.corpus / 'files/file-source-manifest.jsonl'
        row = json.loads(path.read_text())
        row.update(category='media-only', processing={'status': 'audio_transcripts_available'},
                   audio_transcripts={'catalog': 'audio/catalog.json',
                                      'catalog_sha256': reader.sha(self.corpus / 'audio/catalog.json')})
        path.write_text(json.dumps(row) + '\n')

    def test_full_verifier_checks_coverage_and_file_membership(self):
        self.advertise()
        result = reader.verify(self.corpus, self.originals)
        self.assertEqual((result['sources'], result['versions'], result['segments'], result['evidence_files']),
                         (1, 2, 4, 6))
        (self.corpus / 'audio/unaccounted.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'unaccounted'):
            reader.verify(self.corpus, self.originals)

    def test_manifest_pin_prevents_reading_replaced_catalog(self):
        self.advertise()
        self.source['title'] = 'Replaced catalog'
        self.save_catalog()
        with self.assertRaisesRegex(ValueError, 'pins another'):
            self.load()
        with self.assertRaisesRegex(ValueError, 'pin the audio catalog'):
            reader.verify(self.corpus, self.originals)

    def test_missing_catalog_and_pending_metadata_do_not_pass(self):
        self.advertise()
        path = self.corpus / 'files/file-source-manifest.jsonl'
        row = json.loads(path.read_text())
        row['processing']['status'] = 'media_transcript_pending'
        path.write_text(json.dumps(row))
        with self.assertRaisesRegex(ValueError, 'pin the audio catalog'):
            reader.verify(self.corpus, self.originals)
        (self.corpus / 'audio/catalog.json').unlink()
        with self.assertRaises((ValueError, OSError)):
            reader.verify(self.corpus, self.originals)

    def test_unlisted_original_audio_does_not_pass(self):
        self.advertise()
        path = self.corpus / 'files/file-source-manifest.jsonl'
        row = json.loads(path.read_text())
        row['source_id'] = 'missing-audio'
        with path.open('a') as stream:
            stream.write(json.dumps(row) + '\n')
        with self.assertRaisesRegex(ValueError, 'coverage differs'):
            reader.verify(self.corpus, self.originals)

    def test_exact_original_times_and_separate_rechecks(self):
        source = self.load()
        packet = reader.packet(source, start=10, end=14, version='recheck-01')
        self.assertEqual([r['start_seconds'] for r in packet['segments']], [10, 12])
        self.assertEqual(packet['related_rechecks'][0]['interpretation'], 'A separate check, not a correction.')
        full = reader.packet(source)
        self.assertEqual(full['segments'][0]['start_seconds'], 0)

    def test_whole_segments_and_pinned_pagination(self):
        source = self.load()
        first = reader.packet(source, limit=1)
        with self.assertRaises(ValueError):
            reader.packet(source, offset=first['next_offset'])
        second = reader.packet(source, offset=1, expected=first['content_sha256'])
        self.assertEqual(first['segments'] + second['segments'], source['versions'][0]['segments'])
        self.assertIsNone(second['next_offset'])
        with self.assertRaises(ValueError):
            reader.packet(source, start=1, offset=1, expected=first['content_sha256'])

    def test_catalog_change_invalidates_saved_identity(self):
        _, identity = reader.catalog(self.corpus)
        self.source['title'] = 'Changed'
        self.save_catalog()
        with self.assertRaises(ValueError):
            reader.catalog(self.corpus, identity['catalog_sha256'])

    def test_duplicate_catalog_sources_fail_before_body_reads(self):
        self.write('audio/catalog.json', dict(schema='hormozi-original-audio/v1', sources=[self.source, self.source]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            reader.catalog(self.corpus)

    def test_full_version_identity_is_not_guessed(self):
        self.source['versions'][0]['id'] = 'not-full'
        self.save_catalog()
        with self.assertRaisesRegex(ValueError, 'full version ID'):
            self.load()

    def test_invalid_transcript_times_rejected_even_with_updated_hashes(self):
        version = self.source['versions'][0]
        transcript = self.write(version['transcript']['path'], {'segments': [
            {'start': 5, 'end': 6, 'text': 'first'}, {'start': 1, 'end': 3, 'text': 'out of order'}]})
        receipt = json.loads((self.corpus / version['receipt']['path']).read_text())
        receipt['transcript_sha256'] = transcript['sha256']
        version['receipt'] = self.write(version['receipt']['path'], receipt)
        version['transcript'] = transcript
        self.review['transcript_sha256'] = transcript['sha256']
        self.source['review'] = self.write('audio/review.json', self.review)
        self.save_catalog()
        with self.assertRaisesRegex(ValueError, 'out of order'):
            self.load()

    def test_original_and_transcript_tampering_fail(self):
        path = self.originals / 'source.wav'
        path.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'Original audio changed'):
            self.load()
        path.write_bytes(b'fictional original')
        (self.corpus / 'audio/full-transcript.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'evidence changed'):
            self.load()

    def test_missing_recheck_is_not_silently_ignored(self):
        self.source['versions'].pop()
        self.save_catalog()
        with self.assertRaisesRegex(ValueError, 'every reviewed recheck'):
            self.load()

    def test_wrong_original_manifest_fails(self):
        (self.corpus / 'files/file-source-manifest.jsonl').write_text('{}\n')
        with self.assertRaises((ValueError, KeyError)):
            self.load()

    def test_audio_only_rule_rejects_hidden_video_stream(self):
        version = self.source['versions'][0]
        path = self.corpus / version['receipt']['path']
        receipt = json.loads(path.read_text())
        receipt['original_probe']['streams'].append({'codec_type': 'video'})
        version['receipt'] = self.write(version['receipt']['path'], receipt)
        self.save_catalog()
        with self.assertRaisesRegex(ValueError, 'audio streams only'):
            self.load()

    def test_search_and_span_keep_full_original_segments(self):
        source = self.load()
        found = reader.packet(source, query='PRICE clear')
        self.assertEqual(len(found['segments']), 1)
        self.assertEqual(found['segments'][0]['text'], 'Keep the price clear.')
        self.assertEqual(reader.packet(source, query='unmatched')['segments'], [])
        self.assertEqual(len(reader.packet(source, start=1, end=1.5)['segments']), 1)
        with self.assertRaises(ValueError):
            reader.packet(source, query='!!!')

    def test_invalid_times_offsets_and_segment_budget(self):
        source = self.load()
        for values in ({'start': float('nan')}, {'end': float('inf')}, {'start': -1},
                       {'start': True}, {'start': 4, 'end': 1}, {'offset': 100}, {'max_chars': 1},
                       {'limit': True}, {'max_chars': 3.5}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                reader.packet(source, **values)

    def test_paths_cannot_escape_roots(self):
        self.source['relative_path'] = '../outside.wav'
        self.save_catalog()
        manifest = self.corpus / 'files/file-source-manifest.jsonl'
        row = json.loads(manifest.read_text())
        row['relative_path'] = self.source['relative_path']
        manifest.write_text(json.dumps(row))
        with self.assertRaises(ValueError):
            self.load()


if __name__ == '__main__':
    unittest.main()
