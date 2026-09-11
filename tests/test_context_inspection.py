"""Context discovery must not turn incomplete profiles into a write or approval."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "skills/hormozi/scripts/business_context.py"
SPEC = importlib.util.spec_from_file_location("context_inspection", SCRIPT)
context = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(context)


class ContextInspectionTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), "inspect", *map(str, args)],
                              capture_output=True, text=True, check=False)

    def test_draft_context_is_available_without_approval_or_any_write(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            profile = root / "BUSINESS.md"
            profile.write_text("# North Studio\nStatus: draft\n## Offer\nA paid class.\n"
                               "[Rates](rates.md) [Lost](missing.md)\n")
            (root / "rates.md").write_text("Draft price: $80 per class.\n")
            sidecar = root / ".hormozi/business.json"
            sidecar.parent.mkdir()
            sidecar.write_text('{"keep": "existing state"}\n')
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            result = self.run_cli("--profile", profile)
            self.assertEqual(result.returncode, 0, result.stderr)
            record = json.loads(result.stdout)
            self.assertTrue(record["found"])
            self.assertFalse(record["validation"]["approved"])
            self.assertFalse(record["validation"]["valid"])
            self.assertFalse(record["facts_verified"])
            self.assertEqual(record["context_status"], "needs_review")
            self.assertEqual(record["authorities"], [])
            self.assertFalse(record["authorities_checked"])
            self.assertEqual(len(record["authority_links"]), 2)
            self.assertNotIn("Draft price", result.stdout)
            self.assertEqual(before, {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()})
            with self.assertRaises(context.ProfileError):
                context.resolve_profile(profile)

    def test_absence_is_reported_without_searching_siblings_or_creating_profile(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            current = root / "current"
            sibling = root / "other"
            current.mkdir()
            sibling.mkdir()
            (sibling / "BUSINESS.md").write_text("Private neighboring business")
            result = self.run_cli("--start", current)
            self.assertEqual(result.returncode, 0)
            record = json.loads(result.stdout)
            self.assertFalse(record["found"])
            self.assertEqual(record["context_status"], "missing")
            self.assertTrue(record["read_only"])
            self.assertEqual(list(current.iterdir()), [])
            self.assertNotIn("neighboring", result.stdout)

    def test_explicit_missing_profile_does_not_fall_back_to_parent(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "BUSINESS.md").write_text("Do not use me")
            result = self.run_cli("--start", root, "--profile", root / "absent.md")
            self.assertEqual(result.returncode, 2)
            self.assertIn("profile not found", json.loads(result.stdout)["error"])
            self.assertFalse((root / ".hormozi").exists())

    def test_nearest_profile_and_changed_authority_are_read_fresh(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project = root / "project"
            project.mkdir()
            profile = root / "BUSINESS.md"
            profile.write_text("# Draft\n[Rates](rates.md)\n")
            rates = root / "rates.md"
            rates.write_text("Old price")
            first = json.loads(self.run_cli("--start", project, "--check-authorities").stdout)
            rates.write_text("New price")
            second = json.loads(self.run_cli("--start", project, "--check-authorities").stdout)
            self.assertEqual(first["profile"]["path"], str(profile.resolve()))
            self.assertNotEqual(first["authorities"][0]["sha256"], second["authorities"][0]["sha256"])
            self.assertFalse((root / ".hormozi").exists())

    def test_unreadable_authority_does_not_hide_other_context(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            profile = root / "BUSINESS.md"
            profile.write_text("# Draft\n[Blocked](blocked.md) [Fine](fine.md)\n")
            blocked = root / "blocked.md"
            blocked.write_text("Private")
            (root / "fine.md").write_text("Available")
            real_record = context.file_record

            def read_record(path):
                if path == blocked.resolve():
                    raise PermissionError("do not include sensitive error text")
                return real_record(path)

            with patch.object(context, "file_record", side_effect=read_record):
                result = context.inspect_profile(profile, check_authorities=True)
            self.assertEqual([a["status"] for a in result["authorities"]], ["unreadable", "available"])
            self.assertNotIn("sensitive error", json.dumps(result))


    def test_light_inspection_never_opens_linked_files(self):
        with tempfile.TemporaryDirectory() as raw:
            profile = Path(raw) / "BUSINESS.md"
            profile.write_text("# Draft\n[Rates](rates.md)\n")
            with patch.object(context, "authority_records", side_effect=AssertionError("must not read links")):
                result = context.inspect_profile(profile)
            self.assertEqual(result["authority_links"][0]["target"], "rates.md")
            self.assertFalse(result["authorities_checked"])

    def test_explicit_profile_from_attached_repository(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            workspace, app = root / "business", root / "app"
            workspace.mkdir()
            app.mkdir()
            profile = workspace / "BUSINESS.md"
            profile.write_text("# Business\nStatus: draft\n")
            result = self.run_cli("--start", app, "--profile", profile)
            self.assertEqual(json.loads(result.stdout)["profile"]["path"], str(profile.resolve()))
            self.assertEqual(list(app.iterdir()), [])

if __name__ == "__main__":
    unittest.main()
