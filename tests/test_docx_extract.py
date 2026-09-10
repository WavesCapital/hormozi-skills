import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import warnings
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/hormozi/scripts/docx_extract.py'
spec = importlib.util.spec_from_file_location('native_word', SCRIPT)
word = importlib.util.module_from_spec(spec)
spec.loader.exec_module(word)
reader_spec = importlib.util.spec_from_file_location('word_corpus', SCRIPT.with_name('corpus.py'))
reader = importlib.util.module_from_spec(reader_spec)
reader_spec.loader.exec_module(reader)
W, R = word.W, word.R


class DocxExtractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.original = self.root / 'source.docx'
        self.derived = self.root / 'staging'

    def make(self, body, rels='', extras=None):
        document = f'<w:document xmlns:w="{W}" xmlns:r="{R}" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><w:body>{body}<w:sectPr/></w:body></w:document>'
        with zipfile.ZipFile(self.original, 'w') as archive:
            archive.writestr('word/document.xml', document)
            if rels:
                archive.writestr('word/_rels/document.xml.rels', f'<Relationships>{rels}</Relationships>')
            for name, data in (extras or {}).items():
                archive.writestr(name, data)
        self.source = {'source_id': 'fictional:1234', 'source_path': '$HORMOZI_SOURCE_ROOT/source.docx',
                       'sha256': hashlib.sha256(self.original.read_bytes()).hexdigest()}

    def extract(self):
        return word.extract(self.source, self.original, self.derived)

    def reader_fixture(self):
        self.make('<w:p><w:r><w:t>Native first</w:t></w:r></w:p><w:p><w:r><w:t>Native next</w:t></w:r></w:p>')
        self.derived = self.root / 'corpus/files/derived'
        native, processing = self.extract()
        converted = {'format': 'docx', 'source_id': self.source['source_id'], 'source_sha256': self.source['sha256'],
                     'locator': 'file:fictional:1234:p0001', 'page': 1, 'search_text': 'Converted page',
                     'citation': {'source_id': self.source['source_id'], 'original_sha256': self.source['sha256'], 'page': 1}}
        self.record_file = self.root / 'corpus/files/records.jsonl'
        self.source_records = [converted] + native
        self.manifest = {**self.source, 'relative_path': 'source.docx', 'private_records': 'records.jsonl',
                         'record_count': 3, 'processing': processing}
        self.write_reader_fixture()
        return native

    def write_reader_fixture(self):
        self.record_file.write_text(''.join(json.dumps(row) + '\n' for row in self.source_records))
        (self.record_file.parent / 'file-source-manifest.jsonl').write_text(json.dumps(self.manifest) + '\n')

    def test_reader_keeps_native_and_page_navigation_separate(self):
        native = self.reader_fixture()
        page = reader.private_file_records(self.root / 'corpus', 'file:fictional:1234:p0001', 1, None)
        self.assertEqual(page['source_order_basis'], 'converted_pages')
        self.assertIsNone(page['next_locator'])
        self.assertEqual(len(page['records']), 1)
        packet = reader.private_file_records(self.root / 'corpus', native[0]['locator'], 1, None)
        self.assertEqual(packet['source_order_basis'], 'word_native_body_blocks')
        self.assertIsNone(packet['previous_locator'])
        self.assertEqual(packet['next_locator'], native[1]['locator'])
        self.assertEqual(packet['source_record_count'], 3)
        self.assertEqual([r['text'] for r in packet['records']], ['Native first', 'Native next'])
        self.assertIn('not a PDF', packet['citation_target']['location_basis'])

    def test_reader_rejects_native_source_part_and_block_mismatch(self):
        native = self.reader_fixture()
        self.source_records[1]['docx_native']['part_sha256'] = '0' * 64
        self.write_reader_fixture()
        with self.assertRaises(ValueError):
            reader.private_file_records(self.root / 'corpus', native[0]['locator'], 0, None)

    def test_reader_rejects_changed_catalog(self):
        native = self.reader_fixture()
        catalog = self.derived / self.manifest['processing']['native_asset_manifest']
        catalog.write_text('{}')
        with self.assertRaises(ValueError):
            reader.private_file_records(self.root / 'corpus', native[0]['locator'], 0, None)

    def test_reader_rejects_duplicate_locators_across_views(self):
        native = self.reader_fixture()
        self.source_records[0]['locator'] = native[0]['locator']
        self.write_reader_fixture()
        with self.assertRaises(ValueError):
            reader.private_file_records(self.root / 'corpus', native[0]['locator'], 0, None)

    def test_named_source_search_covers_both_reading_groups(self):
        native = self.reader_fixture()
        result = reader.query_private_file(self.root / 'corpus', self.source['source_id'], 'Native', 10)
        self.assertEqual(set(result['locators']), {r['locator'] for r in self.source_records})
        self.assertEqual({r['locator'] for r in result['results']}, {r['locator'] for r in native})
        converted = reader.query_private_file(self.root / 'corpus', self.source['source_id'], 'Converted', 10)
        self.assertEqual([r['locator'] for r in converted['results']], ['file:fictional:1234:p0001'])

    def test_native_blocks_keep_stable_ordinals_and_source_identity(self):
        self.make('<w:p/><w:p><w:r><w:t>Actual text</w:t></w:r></w:p>')
        before = self.original.read_bytes()
        rows, result = self.extract()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['locator'], 'file:fictional:1234:s0002')
        self.assertEqual(rows[0]['docx_native']['paragraphs_zero_based'], [1])
        self.assertEqual(rows[0]['search_text'], 'Actual text')
        self.assertEqual(rows[0]['citation']['original_sha256'], self.source['sha256'])
        self.assertNotIn('page', rows[0]['citation'])
        self.assertEqual(self.original.read_bytes(), before)
        manifest = self.derived / result['native_asset_manifest']
        self.assertEqual(word.sha(manifest.read_bytes()), result['native_asset_manifest_sha256'])

    def test_table_cell_relationships_and_merges_survive(self):
        self.make('<w:tbl><w:tr><w:tc><w:tcPr><w:gridSpan w:val="2"/><w:vMerge w:val="restart"/></w:tcPr><w:p><w:r><w:t>Established business</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Startup</w:t></w:r></w:p></w:tc></w:tr></w:tbl>')
        rows, _ = self.extract()
        table = rows[0]['docx_native']['tables'][0]
        self.assertEqual([c['text'] for c in table['cells']], ['Established business', 'Startup'])
        self.assertEqual(table['cells'][0]['grid_span'], '2')
        self.assertEqual(table['cells'][0]['vertical_merge'], 'restart')
        self.assertEqual(rows[0]['search_text'].count('Established business'), 1)
        self.assertTrue(rows[0]['visual_dependency'])

    def test_nested_tables_preserve_each_text_once_in_search(self):
        self.make('<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Outer label</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>Inner label</w:t></w:r></w:p></w:tc></w:tr></w:tbl></w:tc></w:tr></w:tbl>')
        row = self.extract()[0][0]
        self.assertEqual(row['search_text'].count('Outer label'), 1)
        self.assertEqual(row['search_text'].count('Inner label'), 1)
        self.assertEqual(len(row['docx_native']['tables']), 2)

    def test_strike_false_hidden_and_revision_marks_are_distinct(self):
        self.make('<w:p><w:r><w:rPr><w:strike/></w:rPr><w:t>old price</w:t></w:r><w:r><w:rPr><w:strike w:val="0"/></w:rPr><w:t>new price</w:t></w:r><w:r><w:rPr><w:vanish/></w:rPr><w:t>hidden</w:t></w:r><w:del><w:r><w:delText>removed</w:delText></w:r></w:del><w:ins><w:r><w:t>added</w:t></w:r></w:ins></w:p>')
        text = self.extract()[0][0]['search_text']
        self.assertIn('[crossed out: old price]', text)
        self.assertNotIn('[crossed out: new price]', text)
        self.assertIn('[hidden text: hidden]', text)
        self.assertIn('[deleted: removed]', text)
        self.assertIn('[inserted: added]', text)

    def test_lists_retain_identity_without_inventing_visible_numbers(self):
        self.make('<w:p><w:pPr><w:numPr><w:ilvl w:val="2"/><w:numId w:val="7"/></w:numPr></w:pPr><w:r><w:t>List item</w:t></w:r></w:p>')
        row = self.extract()[0][0]
        self.assertEqual(row['docx_native']['lists'][0]['numId'], '7')
        self.assertIn('label not rendered', row['search_text'])
        self.assertTrue(row['docx_native']['warnings'])

    def test_image_bytes_and_unreferenced_assets_are_preserved(self):
        self.make('<w:p><w:r><w:drawing><a:blip r:embed="image1"/></w:drawing></w:r></w:p>',
                  '<Relationship Id="image1" Target="media/picture.png" Type="image"/>',
                  {'word/media/picture.png': b'fixture image', 'word/media/unreferenced.png': b'other fixture'})
        rows, result = self.extract()
        manifest = json.loads((self.derived / result['native_asset_manifest']).read_text())
        self.assertEqual(len(manifest['images']), 2)
        self.assertEqual(len(rows[0]['docx_native']['images']), 1)
        for asset in manifest['images']:
            self.assertEqual(word.sha((self.derived / asset['path']).read_bytes()), asset['sha256'])

    def test_external_links_and_images_are_recorded_not_fetched(self):
        self.make('<w:p><w:hyperlink r:id="link1"><w:r><w:t>Read this</w:t></w:r></w:hyperlink><w:r><a:blip r:link="image1"/></w:r></w:p>',
                  '<Relationship Id="link1" Target="https://example.invalid/page" TargetMode="External"/><Relationship Id="image1" Target="https://example.invalid/picture" TargetMode="External"/>')
        row = self.extract()[0][0]
        self.assertEqual(len(row['docx_native']['links']), 2)
        self.assertEqual(row['docx_native']['images'], [])
        self.assertIn('not fetched', row['search_text'])

    def test_alternate_content_is_not_counted_twice(self):
        self.make('<w:p><mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"><mc:Choice><w:r><w:t>Chosen</w:t></w:r></mc:Choice><mc:Fallback><w:r><w:t>Fallback</w:t></w:r></mc:Fallback></mc:AlternateContent></w:p>')
        row = self.extract()[0][0]
        self.assertEqual(row['search_text'], 'Chosen')
        self.assertTrue(row['docx_native']['warnings'])

    def test_wrong_source_hash_fails_without_staging_writes(self):
        self.make('<w:p/>')
        self.source['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            self.extract()
        self.assertFalse(self.derived.exists())

    def test_archive_entity_encoding_and_path_attacks_fail(self):
        for raw in (b'<!DOCTYPE a [<!ENTITY b "x">]><a>&b;</a>', '<a/>'.encode('utf-16')):
            with self.assertRaises(ValueError):
                word.xml(raw)
        for target in ('../../outside', '/outside', '%2e%2e/%2e%2e/outside', 'media/%00x', 'https://example.invalid/a'):
            with self.subTest(target=target), self.assertRaises(ValueError):
                word.member('word/document.xml', target)

    def test_duplicate_zip_entries_and_dangling_images_fail(self):
        self.make('<w:p/>')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with zipfile.ZipFile(self.original, 'a') as archive:
                archive.writestr('word/document.xml', '<x/>')
        self.source['sha256'] = word.sha(self.original.read_bytes())
        with self.assertRaises(ValueError):
            self.extract()
        self.make('<w:p><a:blip r:embed="image1"/></w:p>', '<Relationship Id="image1" Target="media/missing.png"/>')
        with self.assertRaises(ValueError):
            self.extract()
        self.assertFalse(self.derived.exists())

    def test_output_symlink_escape_is_rejected(self):
        self.make('<w:p/>')
        self.derived.mkdir()
        outside = self.root / 'outside'
        outside.mkdir()
        (self.derived / 'docx-assets').symlink_to(outside)
        with self.assertRaises(ValueError):
            self.extract()
        self.assertEqual(list(outside.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
