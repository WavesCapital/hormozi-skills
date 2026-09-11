from __future__ import annotations

import base64
import json
import unittest
from unittest.mock import patch

import test_video_source as fixture

video = fixture.video

class SourceHandleTests(unittest.TestCase):
    setUp = fixture.VideoSourceTests.setUp
    save = fixture.VideoSourceTests.save
    args = fixture.VideoSourceTests.args
    run_source = fixture.VideoSourceTests.run_source
    assert_raw_not_read = fixture.VideoSourceTests.assert_raw_not_read
    def by_handle(self, handle, action="read", *extra):
        args = [action, "--handle", handle]
        if action == "read":
            args += ["--start-ms", "0", "--end-ms", "3500"]
        return video.execute(video.parser().parse_args(args + list(extra)))

    def test_handle_keeps_source_when_daily_pointer_changes(self):
        first = self.run_source()
        self.pointer.write_text('{"snapshot_id":"new","manifest_sha256":"unknown"}')
        again = self.by_handle(first["source_handle"])
        self.assertEqual(first["records"], again["records"])
        self.assertEqual(first["raw_sha256"], again["raw_sha256"])

    def test_handle_conflicts_fail_before_any_source_read(self):
        handle = self.run_source()["source_handle"]
        for extra in (("--after", "2020-01-01T00:00:00Z"), ("--include-shorts",),
                      ("--video-id", "otherid1234"), ("--corpus-root", "/tmp/other")):
            with patch.object(video, "load_snapshot", side_effect=AssertionError("read too soon")):
                with self.assertRaises(ValueError):
                    self.by_handle(handle, "read", *extra)

    def test_handle_rechecks_raw_integrity(self):
        handle = self.run_source()["source_handle"]
        self.raw.write_text(self.raw.read_text().replace("Introduction", "Changed intro"))
        with self.assertRaisesRegex(ValueError, "hash changed"):
            self.by_handle(handle)

    def test_handle_does_not_replace_metadata_scope_check(self):
        handle = self.run_source()["source_handle"]
        data = json.loads(base64.urlsafe_b64decode(handle))
        self.row["content_type"] = "short"
        self.save()
        data["fields"]["expected_manifest_sha256"] = self.manifest_hash
        changed = base64.urlsafe_b64encode(json.dumps(data).encode()).decode()
        self.assert_raw_not_read(lambda: self.by_handle(changed), "short_excluded")

    def test_bad_handles_fail_cleanly(self):
        for token in ("bad", "e30=", "x" * 17000,
                      base64.urlsafe_b64encode(b'{"version":1,"fields":[],"include_shorts":false}').decode()):
            with self.assertRaisesRegex(ValueError, "invalid source handle"):
                self.by_handle(token)

    def test_metadata_handle_stays_body_free_until_selected(self):
        result = self.run_source("list")
        with self.assertRaisesRegex(ValueError, "video-id"):
            self.by_handle(result["source_handle"])
        self.assertEqual(len(self.by_handle(result["source_handle"], "read", "--video-id", "abcdef12345")["records"]), 4)

    def test_handle_paging_preserves_content_pin(self):
        first = self.by_handle(self.run_source()["source_handle"], "read", "--limit", "2")
        last = self.by_handle(first["source_handle"], "read", "--offset", "2",
                              "--expected-content-sha256", first["content_sha256"])
        self.assertEqual(len(first["records"] + last["records"]), 4)
        with self.assertRaisesRegex(ValueError, "continued reads require"):
            self.by_handle(first["source_handle"], "read", "--offset", "2")
