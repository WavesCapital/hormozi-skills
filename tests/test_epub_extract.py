"""Native EPUB semantics and reader tests; all inputs are fictional fixtures."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from test_core import corpus

SPEC = importlib.util.spec_from_file_location(
    "epub_extract", Path(__file__).resolve().parents[1] / "skills/hormozi/scripts/epub_extract.py")
epub = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(epub)


class EpubTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.original = self.root / "fixture.epub"
        self.library = self.root / "corpus"
        self.derived = self.library / "files/derived"
        self.members = {
            "META-INF/container.xml": '<container><rootfiles><rootfile full-path="OPS/content.opf"/></rootfiles></container>',
            "OPS/content.opf": '<package><manifest>'
                '<item id="a" href="a.xhtml" media-type="application/xhtml+xml"/>'
                '<item id="z" href="z.xhtml" media-type="application/xhtml+xml"/>'
                '<item id="n" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
                '<item id="i" href="images/chart.svg" media-type="image/svg+xml"/>'
                '</manifest><spine><itemref idref="z"/><itemref idref="a"/></spine></package>',
            "OPS/toc.ncx": '<ncx><navMap><navPoint><navLabel><text>First lesson</text></navLabel>'
                '<content src="z.xhtml#start"/></navPoint><navPoint><navLabel><text>Second lesson</text></navLabel>'
                '<content src="a.xhtml"/></navPoint></navMap></ncx>',
            "OPS/z.xhtml": '<html><head><link rel="stylesheet" href="style.css"/></head>'
                '<body><p>Pay <span class="cut">$240</span> $180 yearly.</p>'
                '<ol class="alpha"><li>Choose a plan<ol start="3"><li>Check costs</li></ol></li>'
                '<li>Check the result</li></ol><img src="images/chart.svg" alt="Fictional chart"/>'
                '<p hidden="hidden">Draft only</p></body></html>',
            "OPS/a.xhtml": '<html><head><title>Fallback title</title></head><body><p>Later lesson.</p></body></html>',
            "OPS/style.css": '.cut {text-decoration:line-through} .alpha {list-style-type:lower-alpha}',
            "OPS/images/chart.svg": '<svg xmlns="http://www.w3.org/2000/svg"><text x="0" y="10">10</text></svg>',
        }

    def build(self):
        with zipfile.ZipFile(self.original, "w") as archive:
            for name, data in self.members.items():
                archive.writestr(name, data)
        self.source = {"source_id": "fixture:abc", "sha256": epub.digest(self.original.read_bytes()),
                       "source_path": str(self.original), "relative_path": "fixture.epub"}

    def extract(self):
        self.build()
        return epub.extract(self.source, self.original, self.derived)

    def save_reader(self, rows):
        records = self.derived / "records/fixture/pages.jsonl"
        records.parent.mkdir(parents=True, exist_ok=True)
        records.write_text("".join(json.dumps(row) + "\n" for row in rows))
        manifest = {**self.source, "private_records": "derived/records/fixture/pages.jsonl", "record_count": len(rows)}
        (self.library / "files/file-source-manifest.jsonl").write_text(json.dumps(manifest) + "\n")

    def test_native_order_preserves_stable_ids_and_titles(self):
        rows, processing = self.extract()
        self.assertEqual([r["section_path"] for r in rows], ["OPS/a.xhtml", "OPS/z.xhtml"])
        self.assertEqual([r["section"] for r in rows], [1, 2])
        self.assertEqual([r["reading_order"] for r in rows], [2, 1])
        self.assertEqual(rows[1]["chapter_titles"], ["First lesson"])
        self.assertEqual(processing["status"], "ok")
        self.assertEqual(processing["spine_count"], 2)
        self.assertEqual(processing["asset_manifest_sha256"], epub.digest((self.derived / processing["asset_manifest"]).read_bytes()))

    def test_semantic_marks_lists_and_images_are_preserved(self):
        rows, _ = self.extract()
        first = rows[1]
        self.assertIn("Pay [crossed out: $240] $180 yearly.", first["search_text"])
        self.assertIn("a. Choose a plan\n  3. Check costs", first["search_text"])
        self.assertIn("b. Check the result", first["search_text"])
        self.assertIn("[hidden source content: Draft only]", first["search_text"])
        self.assertIn("[Image: OPS/images/chart.svg; alt: Fictional chart]", first["search_text"])
        asset = first["epub_images"][0]
        self.assertEqual((self.derived / asset["path"]).read_bytes(), self.members["OPS/images/chart.svg"].encode())
        self.assertEqual(first["visual_review_status"], "native_assets_available_not_reviewed")

    def test_reverse_value_and_native_strike(self):
        self.members["OPS/a.xhtml"] = '<html><body><s>old</s><ol reversed="reversed" type="I"><li>Two</li><li value="5">Five</li><li>Four</li></ol></body></html>'
        rows, _ = self.extract()
        self.assertIn("[crossed out: old]", rows[0]["search_text"])
        for marker in ("III. Two", "V. Five", "IV. Four"):
            self.assertIn(marker, rows[0]["search_text"])

    def test_css_cascade_and_unsupported_selector_are_explicit(self):
        self.members["OPS/style.css"] += ' .cut {text-decoration:none} #price {text-decoration:line-through !important} p > span {visibility:hidden}'
        self.members["OPS/z.xhtml"] = self.members["OPS/z.xhtml"].replace('class="cut"', 'class="cut" id="price" style="text-decoration:none"')
        rows, processing = self.extract()
        self.assertIn("[crossed out: $240]", rows[1]["search_text"])
        self.assertEqual(processing["status"], "ok_with_warnings")
        self.assertTrue(any("p > span" in w for w in rows[1]["extraction_warnings"]))

    def test_nonspine_content_retained_at_end(self):
        self.members["bonus.xhtml"] = '<html><body><h1>Bonus</h1><p>Keep this.</p></body></html>'
        rows, _ = self.extract()
        self.assertEqual(rows[2]["reading_order"], 3)
        self.assertIsNone(rows[2]["spine_position"])
        self.assertEqual(rows[2]["chapter_titles"], ["Bonus"])

    def test_bad_spine_missing_asset_and_bad_list_fail(self):
        original = copy.deepcopy(self.members)
        changes = [
            ("OPS/content.opf", original["OPS/content.opf"].replace('idref="a"', 'idref="z"'), "spine"),
            ("OPS/z.xhtml", '<html><body><img src="images/missing.png"/></body></html>', "image missing"),
            ("OPS/a.xhtml", '<html><body><ol>Lost text<li>One</li></ol></body></html>', "outside list"),
        ]
        for path, value, message in changes:
            with self.subTest(message=message):
                self.members = {**original, path: value}
                with self.assertRaisesRegex(ValueError, message):
                    self.extract()

    def test_hash_mismatch_has_no_writes(self):
        self.build()
        self.source["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            epub.extract(self.source, self.original, self.derived)
        self.assertFalse(self.derived.exists())

    def test_remote_and_escaping_references_fail(self):
        for href in ("https://example.com/a", "//example.com/a", "../../outside", "/absolute", "%2e%2e/%2e%2e/out", "x%00.png", "x%5cy.png", "file:///tmp/x"):
            with self.subTest(href=href), self.assertRaises(ValueError):
                epub.member_path("OPS/a.xhtml", href)
        self.assertEqual(epub.member_path("OPS/a.xhtml", "images/a%20b.png#x"), "OPS/images/a b.png")

    def test_entities_in_utf8_and_utf16_fail(self):
        text = '<!DOCTYPE a [<!ENTITY x "unsafe">]><a>&x;</a>'
        for data in (text.encode(), text.encode("utf-16"), text.encode("utf-32")):
            with self.subTest(data=data[:8]), self.assertRaises(ValueError):
                epub.xml(data)

    def test_asset_symlink_escape_does_not_write_outside(self):
        outside = self.root / "outside"
        outside.mkdir()
        self.derived.mkdir(parents=True)
        (self.derived / "epub-assets").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "escapes derived"):
            self.extract()
        self.assertEqual(list(outside.iterdir()), [])

    def test_reader_follows_spine_and_returns_checked_assets(self):
        rows, _ = self.extract()
        self.save_reader(rows)
        before = {str(p): epub.digest(p.read_bytes()) for p in self.root.rglob("*") if p.is_file()}
        packet = corpus.private_file_records(self.library, rows[1]["locator"], 1, self.root)
        self.assertEqual([r["locator"] for r in packet["records"]], [rows[1]["locator"], rows[0]["locator"]])
        self.assertIsNone(packet["previous_locator"])
        self.assertEqual(packet["next_locator"], rows[0]["locator"])
        self.assertEqual(packet["source_order_basis"], "epub_spine_then_non_spine")
        self.assertIn("not a physical page", packet["citation_target"]["location_basis"])
        self.assertTrue(packet["original"]["verified"])
        asset = packet["records"][0]["epub_images"][0]
        self.assertTrue(asset["verified"])
        self.assertFalse(asset["visual_reviewed"])
        self.assertEqual(before, {str(p): epub.digest(p.read_bytes()) for p in self.root.rglob("*") if p.is_file()})

    def test_reader_rejects_incomplete_or_duplicate_orders(self):
        rows, _ = self.extract()
        for value in (None, True, 2, "1"):
            mutated = copy.deepcopy(rows)
            mutated[1]["reading_order"] = value
            self.save_reader(mutated)
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "order"):
                corpus.private_file_records(self.library, rows[0]["locator"], 1, None)

    def test_reader_missing_corrupt_and_escaping_asset(self):
        rows, _ = self.extract()
        asset = rows[1]["epub_images"][0]
        asset_path = self.derived / asset["path"]
        self.save_reader(rows)
        asset_path.rename(asset_path.with_suffix(".saved"))
        packet = corpus.private_file_records(self.library, rows[1]["locator"], 0, None)
        self.assertEqual(packet["records"][0]["epub_images"][0]["status"], "missing")
        asset_path.write_bytes(b"corrupted")
        with self.assertRaisesRegex(ValueError, "image hash mismatch"):
            corpus.private_file_records(self.library, rows[1]["locator"], 0, None)
        asset["path"] = "../../outside"
        self.save_reader(rows)
        with self.assertRaisesRegex(ValueError, "escapes"):
            corpus.private_file_records(self.library, rows[1]["locator"], 0, None)

    def test_reader_rejects_broken_native_metadata(self):
        rows, _ = self.extract()
        for key, value in (("package_sha256", {}), ("section_sha256", "bad"),
                           ("section_path", "OPS/z.xhtml"), ("spine_position", 1),
                           ("spine_linear", "maybe")):
            mutated = copy.deepcopy(rows)
            mutated[0][key] = value
            self.save_reader(mutated)
            with self.subTest(key=key), self.assertRaises(ValueError):
                corpus.private_file_records(self.library, rows[0]["locator"], 0, None)

    def test_named_query_finds_chapters_regardless_of_storage_order(self):
        rows, _ = self.extract()
        self.save_reader(rows)
        packet = corpus.query_private_file(self.library, self.source["source_id"], '"First lesson"', 3)
        self.assertEqual(packet["results"][0]["locator"], rows[1]["locator"])
        packet = corpus.query_private_file(self.library, self.source["source_id"], '"Later lesson"', 3)
        self.assertEqual(packet["results"][0]["locator"], rows[0]["locator"])


if __name__ == "__main__":
    unittest.main()
