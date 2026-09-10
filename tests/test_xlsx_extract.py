import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import warnings
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/hormozi/scripts/xlsx_extract.py'
spec = importlib.util.spec_from_file_location('native_workbook', SCRIPT)
book = importlib.util.module_from_spec(spec)
spec.loader.exec_module(book)
reader_spec = importlib.util.spec_from_file_location('xlsx_corpus', SCRIPT.with_name('corpus.py'))
reader = importlib.util.module_from_spec(reader_spec)
reader_spec.loader.exec_module(reader)
S, R = book.S, book.R
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'


class XlsxExtractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.original = self.root / 'source.xlsx'

    def make(self, rows='', trailing='', rels='', extras=None, sheet_name='Test', sheet_state='visible'):
        files = {
            '_rels/.rels': f'<Relationships xmlns="{REL}"><Relationship Id="root" Type="{R}/officeDocument" Target="xl/workbook.xml"/></Relationships>',
            'xl/workbook.xml': f'<workbook xmlns="{S}" xmlns:r="{R}"><workbookPr date1904="1"/><sheets><sheet name="{sheet_name}" sheetId="1" state="{sheet_state}" r:id="sheet"/></sheets></workbook>',
            'xl/_rels/workbook.xml.rels': f'<Relationships xmlns="{REL}"><Relationship Id="sheet" Type="{R}/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="strings" Type="{R}/sharedStrings" Target="sharedStrings.xml"/><Relationship Id="styles" Type="{R}/styles" Target="styles.xml"/></Relationships>',
            'xl/sharedStrings.xml': f'<sst xmlns="{S}"><si><r><rPr><strike/></rPr><t>Old price</t></r><r><t xml:space="preserve"> $90</t></r><rPh><t>phonetic</t></rPh></si></sst>',
            'xl/styles.xml': f'<styleSheet xmlns="{S}"><fonts><font><b/></font></fonts><fills><fill><patternFill patternType="solid"><fgColor rgb="FFFFFF00"/></patternFill></fill></fills><cellXfs><xf fontId="0" fillId="0" numFmtId="0"/></cellXfs></styleSheet>',
            'xl/worksheets/sheet1.xml': f'<worksheet xmlns="{S}" xmlns:r="{R}"><cols><col min="1" max="1" hidden="1"/></cols><sheetData>{rows}</sheetData>{trailing}</worksheet>',
        }
        if rels:
            files['xl/worksheets/_rels/sheet1.xml.rels'] = f'<Relationships xmlns="{REL}">{rels}</Relationships>'
        files.update(extras or {})
        with zipfile.ZipFile(self.original, 'w') as archive:
            for name, data in files.items():
                archive.writestr(name, data)
        self.source = {'source_id': 'fictional:1234', 'source_path': '$HORMOZI_SOURCE_ROOT/source.xlsx',
                       'sha256': hashlib.sha256(self.original.read_bytes()).hexdigest()}

    def extract(self):
        return book.extract(self.source, self.original)

    def reader_fixture(self, prepare=True):
        if prepare:
            self.make('<row r="4"><c r="A4" t="inlineStr"><is><t>Sender color key</t></is></c></row><row r="9"><c r="B9" t="inlineStr"><is><t>Customer receipt</t></is></c></row>')
        self.corpus = self.root / 'corpus'
        self.derived = self.corpus / 'files/derived'
        native, processing = book.stage(self.source, self.original, self.derived)
        converted = {'format': 'xlsx', 'source_id': self.source['source_id'], 'source_sha256': self.source['sha256'],
                     'locator': 'file:fictional:1234:p0001', 'page': 1, 'search_text': 'Converted page',
                     'citation': {'source_id': self.source['source_id'], 'original_sha256': self.source['sha256'], 'page': 1}}
        self.records = [converted] + native
        self.manifest = {**self.source, 'relative_path': 'source.xlsx', 'private_records': 'rows.jsonl',
                         'record_count': len(self.records), 'processing': processing}
        self.write_fixture()
        return native

    def write_fixture(self):
        (self.corpus / 'files/rows.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in self.records))
        (self.corpus / 'files/file-source-manifest.jsonl').write_text(json.dumps(self.manifest) + '\n')

    def test_reader_keeps_workbook_rows_and_converted_pages_separate(self):
        native = self.reader_fixture()
        page = reader.private_file_records(self.corpus, self.records[0]['locator'], 3, None)
        self.assertEqual(page['source_order_basis'], 'converted_pages')
        self.assertIsNone(page['next_locator'])
        self.assertEqual(len(page['records']), 1)
        result = reader.private_file_records(self.corpus, native[1]['locator'], 1, self.root)
        self.assertEqual(result['source_order_basis'], 'workbook_native_sheet_rows')
        self.assertEqual(len(result['records']), 3)
        self.assertTrue(all(r['page'] is None for r in result['records']))
        row = result['records'][1]['xlsx_native']
        self.assertEqual(row['cells'][0]['address'], 'A4')
        self.assertIn('FFFFFF00', str(row['cell_styles']))
        self.assertEqual(result['citation_target']['kind'], 'original_file')
        self.assertIn('cell addresses', result['citation_target']['location_basis'])

    def test_named_workbook_search_covers_both_views(self):
        native = self.reader_fixture()
        result = reader.query_private_file(self.corpus, self.source['source_id'], 'receipt', 10)
        self.assertEqual([r['locator'] for r in result['results']], [native[2]['locator']])
        result = reader.query_private_file(self.corpus, self.source['source_id'], 'Converted', 10)
        self.assertEqual([r['locator'] for r in result['results']], [self.records[0]['locator']])

    def test_packet_shares_metadata_without_losing_cell_context(self):
        self.make(''.join(f'<row r="{i}"><c r="A{i}" t="inlineStr"><is><t>Row {i}</t></is></c>'
                         f'<c r="B{i}" t="s"><v>0</v></c><c r="C{i}"><f>A{i}*2</f></c></row>'
                         for i in range(1, 8)))
        native = self.reader_fixture(prepare=False)
        target = native[4]['locator']
        before = reader.private_file_records(self.corpus, target, 3, None)
        packet = reader.read_source(self.root / 'unused.sqlite', target, corpus_root=self.corpus, context=3)
        self.assertEqual([r['text'] for r in packet['records']], [r['text'] for r in before['records']])
        self.assertEqual(len(packet['records']), 7)
        shared = packet['workbook_context']
        for old, new in zip(before['records'], packet['records']):
            source, compact = old['xlsx_native'], new['xlsx_native']
            self.assertEqual(shared['sheets'][compact['sheet_id']]['column_definitions'], source['column_definitions'])
            for original, cell in zip(source['cells'], compact['cells']):
                for key in ('address', 'text', 'style_index', 'raw_value', 'formula', 'data_type'):
                    self.assertEqual(cell[key], original[key])
                self.assertEqual(shared['cell_styles'][str(cell['style_index'])], source['cell_styles'][str(cell['style_index'])])
                if original.get('rich_text') and any(run['properties'] is not None for run in original['rich_text']['runs']):
                    self.assertEqual(cell['rich_text'], original['rich_text'])
            self.assertNotIn('cell_styles', compact)
        self.assertLess(len(json.dumps(packet)), len(json.dumps(before)))

    def test_paging_pin_rejects_style_change_even_with_same_words(self):
        native = self.reader_fixture()
        target = native[1]['locator']
        packet = reader.read_source(self.root / 'unused.sqlite', target, corpus_root=self.corpus, context=0, max_chars=5)
        path = self.derived / self.manifest['processing']['native_asset_manifest']
        text = path.read_text()
        self.assertIn('FFFFFF00', text)
        path.write_text(text.replace('FFFFFF00', 'FFFF0000'))
        self.manifest['processing']['native_asset_manifest_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.write_fixture()
        with self.assertRaisesRegex(ValueError, 'packet changed'):
            reader.read_source(self.root / 'unused.sqlite', target, corpus_root=self.corpus, context=0,
                               offset=5, expected_content_sha256=packet['content_sha256'])

    def test_shared_context_preserves_text_paging_and_full_metadata_access(self):
        native = self.reader_fixture()
        target = native[1]['locator']
        full = reader.read_source(self.root / 'unused.sqlite', target, corpus_root=self.corpus, context=1)
        pieces = {r['locator']: '' for r in full['records']}
        offset = 0
        while True:
            packet = reader.read_source(self.root / 'unused.sqlite', target, corpus_root=self.corpus, context=1,
                                        offset=offset, max_chars=9, expected_content_sha256=full['content_sha256'])
            self.assertEqual(packet['workbook_context'], full['workbook_context'])
            self.assertEqual(packet['native_workbook_supplement'], full['native_workbook_supplement'])
            for row in packet['records']:
                pieces[row['locator']] += row['text']
            if packet['next_offset'] is None:
                break
            offset = packet['next_offset']
        self.assertEqual(pieces, {r['locator']: r['text'] for r in full['records']})
        self.assertFalse(packet['packet_complete'])

    def test_reader_rejects_changed_native_cells_or_catalog(self):
        native = self.reader_fixture()
        self.records[2]['xlsx_native']['cells'][0]['address'] = 'A400'
        self.write_fixture()
        with self.assertRaisesRegex(ValueError, 'record lineage'):
            reader.private_file_records(self.corpus, native[1]['locator'], 0, None)
        self.reader_fixture()
        path = self.derived / self.manifest['processing']['native_asset_manifest']
        path.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'catalog hash'):
            reader.private_file_records(self.corpus, native[1]['locator'], 0, None)

    def test_native_staging_rejects_asset_directory_symlink_escape(self):
        self.make()
        derived = self.root / 'derived'
        derived.mkdir()
        outside = self.root / 'outside'
        outside.mkdir()
        (derived / 'xlsx-assets').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'escapes'):
            book.stage(self.source, self.original, derived)
        self.assertEqual(list(outside.iterdir()), [])

    def test_reader_omits_unrelated_row_metadata_but_keeps_checked_catalog(self):
        self.make('<row r="4" hidden="1"><c r="A4" t="inlineStr"><is><t>Relevant value</t></is></c></row>',
                  '<hyperlinks><hyperlink ref="A4" location="Relevant!A1"/><hyperlink ref="Z99" location="Unrelated!A1"/></hyperlinks><dataValidations><dataValidation sqref="Z99"><formula1>UNRELATED_RULE</formula1></dataValidation></dataValidations>')
        native = self.reader_fixture(prepare=False)
        result = reader.private_file_records(self.corpus, native[1]['locator'], 0, None)
        row = result['records'][0]['xlsx_native']
        self.assertEqual(row['row_attributes']['hidden'], '1')
        self.assertEqual(row['sheet_hyperlinks'][0]['location'], 'Relevant!A1')
        self.assertNotIn('Unrelated!', json.dumps(row))
        self.assertNotIn('UNRELATED_RULE', json.dumps(row))
        self.assertIn('FFFFFF00', json.dumps(row['cell_styles']))
        catalog = Path(result['native_workbook_supplement']['catalog_path'])
        self.assertIn('UNRELATED_RULE', catalog.read_text())
        self.assertIn('Unrelated!', catalog.read_text())
        self.assertEqual(hashlib.sha256(catalog.read_bytes()).hexdigest(), result['native_workbook_supplement']['catalog_sha256'])

    def test_reader_checks_original_image_bytes_without_claiming_visual_review(self):
        self.make(trailing='<drawing r:id="draw"/>',
                  rels=f'<Relationship Id="draw" Type="{R}/drawing" Target="../drawings/drawing1.xml"/>',
                  extras={'xl/drawings/drawing1.xml': f'<wsDr xmlns="urn:drawing" xmlns:r="{R}"><pic r:embed="img"/></wsDr>',
                          'xl/drawings/_rels/drawing1.xml.rels': f'<Relationships xmlns="{REL}"><Relationship Id="img" Type="{R}/image" Target="../media/image1.png"/></Relationships>',
                          'xl/media/image1.png': b'fixture bytes'})
        native = self.reader_fixture(prepare=False)
        packet = reader.private_file_records(self.corpus, native[0]['locator'], 0, None)
        asset = packet['records'][0]['xlsx_native']['images'][0]
        self.assertTrue(asset['verified'])
        self.assertFalse(asset['visual_reviewed'])
        path = Path(asset['path'])
        path.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'image hash'):
            reader.private_file_records(self.corpus, native[0]['locator'], 0, None)
        path.unlink()
        missing = reader.private_file_records(self.corpus, native[0]['locator'], 0, None)
        self.assertEqual(missing['records'][0]['xlsx_native']['images'][0]['status'], 'missing')
        self.assertFalse(missing['records'][0]['xlsx_native']['images'][0]['verified'])

    def test_row_identity_rich_text_styles_and_numeric_precision(self):
        self.make('<row r="3" hidden="1"><c r="B3" t="s"><v>0</v></c><c r="D3"><v>9007199254740993</v></c><c r="E3" s="0"/></row>',
                  '<mergeCells><mergeCell ref="B3:C3"/></mergeCells>', sheet_state='hidden')
        before = self.original.read_bytes()
        records, catalog, media = self.extract()
        self.assertEqual(len(records), 2)
        row = records[1]['xlsx_native']
        self.assertEqual(row['row'], 3)
        self.assertEqual([c['address'] for c in row['cells']], ['B3', 'D3', 'E3'])
        self.assertEqual(row['cells'][0]['text'], 'Old price $90')
        self.assertIn('strike', str(row['cells'][0]['rich_text']['runs'][0]['properties']))
        self.assertNotIn('phonetic', records[1]['search_text'])
        self.assertIn('[crossed out: Old price]', records[1]['search_text'])
        self.assertEqual(row['cells'][1]['raw_value'], '9007199254740993')
        self.assertEqual(catalog['sheets'][0]['state'], 'hidden')
        self.assertEqual(catalog['sheets'][0]['row_attributes'][0]['hidden'], '1')
        self.assertIn('B3:C3', str(catalog['sheets'][0]['structure']))
        self.assertIn('FFFFFF00', str(catalog['styles']))
        self.assertEqual(self.original.read_bytes(), before)
        self.assertEqual(list(self.root.iterdir()), [self.original])
        self.assertEqual(media, {})

    def test_formulas_and_saved_cache_are_not_recalculation(self):
        self.make('<row r="1"><c r="A1"><f t="shared" si="0" ref="A1:A2">B1*2</f><v>9</v></c></row><row r="2"><c r="A2"><f t="shared" si="0"/></c><c r="B2" t="b"><v>0</v></c></row>')
        records, catalog, _ = self.extract()
        cells = records[1]['xlsx_native']['cells']
        self.assertEqual(cells[0]['formula']['text'], 'B1*2')
        self.assertEqual(cells[0]['raw_value'], '9')
        self.assertIsNone(records[2]['xlsx_native']['cells'][0]['raw_value'])
        self.assertEqual(records[2]['xlsx_native']['cells'][1]['text'], '0')
        self.assertIn('not recalculated', records[1]['search_text'])
        self.assertIn('date1904', str(catalog['workbook_structure']))

    def test_links_notes_and_original_drawing_anchors(self):
        self.make('<row r="1"><c r="A1" t="inlineStr"><is><t>Link</t></is></c></row>',
                  '<hyperlinks><hyperlink ref="A1" r:id="url"/></hyperlinks><drawing r:id="draw"/>',
                  f'<Relationship Id="url" Type="{R}/hyperlink" Target="https://example.org/private" TargetMode="External"/><Relationship Id="note" Type="{R}/comments" Target="../comments/comment1.xml"/><Relationship Id="draw" Type="{R}/drawing" Target="../drawings/drawing1.xml"/>',
                  {'xl/comments/comment1.xml': f'<comments xmlns="{S}"><authors><author>Writer</author></authors><commentList><comment ref="Z99" authorId="0"><text><t>Missing target</t></text></comment></commentList></comments>',
                   'xl/drawings/drawing1.xml': f'<wsDr xmlns="urn:drawing" xmlns:r="{R}"><twoCellAnchor><from><col>1</col><row>2</row></from><pic r:embed="img"/></twoCellAnchor></wsDr>',
                   'xl/drawings/_rels/drawing1.xml.rels': f'<Relationships xmlns="{REL}"><Relationship Id="img" Type="{R}/image" Target="../media/image1.png"/></Relationships>',
                   'xl/media/image1.png': b'original fixture bytes'})
        records, catalog, assets = self.extract()
        self.assertEqual(records[-1]['citation']['cell'], 'Z99')
        self.assertIn('Missing target', records[-1]['search_text'])
        sheet = catalog['sheets'][0]
        self.assertTrue(sheet['hyperlinks'][0]['relationship']['external'])
        self.assertIn('twoCellAnchor', str(sheet['drawings'][0]['xml']))
        image = sheet['drawings'][0]['images'][0]
        self.assertEqual(assets[image['asset_name']], b'original fixture bytes')
        self.assertEqual(image['sha256'], hashlib.sha256(b'original fixture bytes').hexdigest())

    def test_blank_styled_rows_are_preserved_without_fake_content(self):
        self.make('<row r="400" s="0"><c r="B400" s="0"/></row>')
        records, catalog, _ = self.extract()
        self.assertEqual(len(records), 1)
        self.assertEqual(catalog['sheets'][0]['content_cell_count'], 0)
        self.assertEqual(catalog['sheets'][0]['style_only_cells'][0]['address'], 'B400')

    def test_missing_cache_is_distinct_from_zero_or_error(self):
        self.make('<row r="1"><c r="A1"><f>1/0</f></c><c r="B1" t="e"><v>#DIV/0!</v></c><c r="C1"><v>0</v></c></row>')
        cells = self.extract()[0][1]['xlsx_native']['cells']
        self.assertEqual([c['raw_value'] for c in cells], [None, '#DIV/0!', '0'])

    def test_hash_mismatch_fails_without_writes(self):
        self.make()
        self.source['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            self.extract()
        self.assertEqual(list(self.root.iterdir()), [self.original])

    def test_invalid_string_style_and_cell_identity_fail(self):
        for cell in ['<c r="A1" t="s"><v>-1</v></c>', '<c r="A1" s="8"/>',
                     '<c r="A2"/>', '<c r="XFE1"/>', '<c r="A1"/><c r="A1"/>']:
            with self.subTest(cell=cell):
                self.make(f'<row r="1">{cell}</row>')
                with self.assertRaises(ValueError):
                    self.extract()

    def test_bad_relationship_and_entity_fail(self):
        for target in ['../../../outside.xml', 'file:///tmp/outside.xml', '..%2f..%2f..%2foutside.xml']:
            self.make(rels=f'<Relationship Id="bad" Type="{R}/comments" Target="{target}"/>')
            with self.assertRaises(ValueError):
                self.extract()
        self.make(extras={'xl/sharedStrings.xml': b'<!DOCTYPE x [<!ENTITY a "bad">]><x/>'})
        with self.assertRaises(ValueError):
            self.extract()

    def test_package_absolute_target_remains_inside_zip(self):
        self.assertEqual(book.member('xl/workbook.xml', '/xl/worksheets/sheet1.xml'), 'xl/worksheets/sheet1.xml')

    def test_calendar_epochs_fraction_and_fictitious_leap_day(self):
        self.assertEqual(book.calendar_value('45888.0', 'm/d', False), ('2025-08-19 00:00:00', None))
        self.assertEqual(book.calendar_value('1.5', 'yyyy-mm-dd hh:mm', True), ('1904-01-02 12:00:00', None))
        self.assertEqual(book.calendar_value('1', 'm/d', False), ('1900-01-01 00:00:00', None))
        self.assertEqual(book.calendar_value('59', 'm/d', False), ('1900-02-28 00:00:00', None))
        self.assertEqual(book.calendar_value('61', 'm/d', False), ('1900-03-01 00:00:00', None))
        value, warning = book.calendar_value('60.5', 'm/d', False)
        self.assertIsNone(value)
        self.assertIn('fictitious', warning)

    def test_non_dates_and_quoted_date_words_are_not_converted(self):
        for fmt in ['0.00%', '0 "days"', '[$USD]0.00', 'hh:mm', '[h]:mm']:
            self.assertEqual(book.calendar_value('12', fmt, False), (None, None))
        for value in ['NaN', 'Infinity', '-1', 'garbage']:
            self.assertIsNone(book.calendar_value(value, 'm/d', False)[0])

    def test_date_cell_keeps_serial_style_and_iso_date(self):
        self.make('<row r="1"><c r="A1"><v>1.5</v></c></row>', extras={
            'xl/styles.xml': f'<styleSheet xmlns="{S}"><cellXfs><xf numFmtId="22"/></cellXfs></styleSheet>'})
        cell = self.extract()[0][1]['xlsx_native']['cells'][0]
        self.assertEqual(cell['raw_value'], '1.5')
        self.assertEqual(cell['calendar_value'], '1904-01-02 12:00:00')
        self.assertEqual(cell['number_format_id'], 22)

    def test_duplicate_zip_member_rejected(self):
        self.make()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with zipfile.ZipFile(self.original, 'a') as archive:
                archive.writestr('xl/styles.xml', '<x/>')
        self.source['sha256'] = hashlib.sha256(self.original.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.extract()


if __name__ == '__main__':
    unittest.main()
