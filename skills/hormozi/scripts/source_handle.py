"""Portable read-only video source settings; never an authorization credential."""
from __future__ import annotations

import base64
import json
from pathlib import Path


FIELDS = ("corpus_root", "after", "before", "snapshot_id", "expected_manifest_sha256",
          "video_id", "expected_raw_sha256")


def encode(args, result: dict) -> str:
    fields = {key: getattr(args, key, None) for key in FIELDS}
    fields.update(corpus_root=str(Path(args.corpus_root).expanduser().resolve()),
                  snapshot_id=result["snapshot_id"],
                  expected_manifest_sha256=result["manifest_sha256"],
                  expected_raw_sha256=result.get("raw_sha256"))
    payload = {"version": 1, "fields": fields, "include_shorts": bool(args.include_shorts)}
    return base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True).encode()).decode()


def apply(args):
    token = getattr(args, "handle", None)
    if token:
        try:
            if len(token) > 16384:
                raise ValueError("too long")
            payload = json.loads(base64.b64decode(token, altchars=b"-_", validate=True))
            if (not isinstance(payload, dict) or set(payload) != {"version", "fields", "include_shorts"}
                    or type(payload["version"]) is not int or payload["version"] != 1
                    or type(payload["include_shorts"]) is not bool):
                raise ValueError("invalid schema")
            fields = payload["fields"]
            if not isinstance(fields, dict) or set(fields) != set(FIELDS):
                raise ValueError("invalid fields")
            if any(value is not None and not isinstance(value, str) for value in fields.values()):
                raise ValueError("invalid value")
            if not all(fields[k] for k in ("corpus_root", "after", "before", "snapshot_id", "expected_manifest_sha256")):
                raise ValueError("missing source scope")
        except (ValueError, TypeError, UnicodeError) as error:
            raise ValueError("invalid source handle") from error
        for key, saved in fields.items():
            supplied = getattr(args, key, None)
            if supplied is not None and saved is not None and supplied != saved:
                raise ValueError("source handle conflicts with --" + key.replace("_", "-"))
            if supplied is None:
                setattr(args, key, saved)
        if args.include_shorts and not payload["include_shorts"]:
            raise ValueError("source handle does not permit Shorts")
        args.include_shorts = payload["include_shorts"]
    if not all(getattr(args, key, None) for key in ("corpus_root", "after", "before")):
        raise ValueError("provide corpus-root, after and before, or a source handle")
    if args.action != "list" and not args.video_id:
        raise ValueError("video-id is required")
    return args
