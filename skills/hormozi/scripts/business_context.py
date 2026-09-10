#!/usr/bin/env python3
"""Find, validate, and resolve a source-linked BUSINESS.md profile."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


APPROVED_RE = re.compile(
    r"(?im)^(?:[-*]\s*)?(?:\*\*)?status\s*:(?:\*\*)?\s*(?:\*\*)?approved\b"
)
HEADING_RE = re.compile(r"^(#{2,6})\s+(.+?)\s*$", re.MULTILINE)
LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
PLACEHOLDER_RE = re.compile(r"\[(?:name or role|[^\]]*unknown[^\]]*|[^\]]*describe[^\]]*)\]", re.I)

REQUIRED_SECTIONS: dict[str, tuple[tuple[str, ...], ...]] = {
    "identity": (("identity",), ("business", "thesis"), ("business", "model")),
    "customers": (("customer",), ("market",)),
    "expensive_problems": (("expensive", "problem"), ("problem",), ("pain",)),
    "offer": (("offer",), ("mechanism",)),
    "economics": (("economic",), ("money", "model"), ("unit", "economic")),
    "acquisition": (("acquisition",), ("distribution",), ("demand",)),
    "sales": (("sales",), ("conversion",)),
    "delivery": (("delivery",), ("activation",), ("retention",), ("customer", "value")),
    "proof": (("proof",), ("evidence", "standard")),
    "constraint": (("constraint",), ("priorit",), ("limiting", "factor")),
    "boundaries": (("claim",), ("safety",), ("boundar",)),
    "authorities": (("authorit",), ("source", "truth"), ("source", "map"), ("freshness",)),
    "unknowns": (("unknown",),),
}

IGNORED_SCHEMES = ("http://", "https://", "mailto:", "plugin://", "app://", "#")


class ProfileError(Exception):
    """A requested profile operation cannot be completed."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def find_profile(start: Path) -> Path | None:
    current = start.expanduser().resolve()
    if current.is_file():
        current = current.parent
    for directory in (current, *current.parents):
        candidate = directory / "BUSINESS.md"
        if candidate.is_file():
            return candidate
    return None


def split_sections(text: str) -> list[dict[str, str]]:
    matches = list(HEADING_RE.finditer(text))
    sections: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        level = len(match.group(1))
        end = len(text)
        for later in matches[index + 1 :]:
            if len(later.group(1)) <= level:
                end = later.start()
                break
        sections.append(
            {
                "heading": match.group(2).strip(),
                "normalized": re.sub(r"[^a-z0-9]+", " ", match.group(2).lower()).strip(),
                "body": text[match.end() : end].strip(),
            }
        )
    return sections


def section_matches(normalized: str, alternatives: tuple[tuple[str, ...], ...]) -> bool:
    return any(all(token in normalized for token in tokens) for tokens in alternatives)


def validate_profile(path: Path) -> tuple[dict[str, Any], str, list[dict[str, str]]]:
    if not path.is_file():
        raise ProfileError(f"profile not found: {path}")
    text = path.read_text(encoding="utf-8")
    sections = split_sections(text)
    matched: dict[str, dict[str, str]] = {}
    for canonical, alternatives in REQUIRED_SECTIONS.items():
        candidates = [section for section in sections if section_matches(section["normalized"], alternatives)]
        usable = next((section for section in candidates if len(section["body"].strip()) >= 20), None)
        if usable:
            matched[canonical] = usable

    missing = [name for name in REQUIRED_SECTIONS if name not in matched]
    approved = bool(APPROVED_RE.search(text))
    placeholders = sorted(set(PLACEHOLDER_RE.findall(text))) if approved else []
    errors: list[str] = []
    if not approved:
        errors.append("status must be approved")
    if missing:
        errors.append("missing or empty semantic sections: " + ", ".join(missing))
    if placeholders:
        errors.append("approved profile contains unresolved template placeholders")

    result = {
        "schema_version": 1,
        "valid": not errors,
        "approved": approved,
        "errors": errors,
        "missing_sections": missing,
        "matched_sections": {
            canonical: {
                "heading": section["heading"],
                "content_sha256": hashlib.sha256(section["body"].encode("utf-8")).hexdigest(),
            }
            for canonical, section in matched.items()
        },
    }
    return result, text, sections


def clean_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    target = target.split("#", 1)[0]
    return target.replace("%20", " ")


def authority_records(profile: Path, text: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    by_resolved_path: dict[str, dict[str, Any]] = {}
    for label, raw_target in LINK_RE.findall(text):
        target = clean_target(raw_target)
        if not target or target.lower().startswith(IGNORED_SCHEMES):
            continue
        candidate = Path(os.path.expandvars(os.path.expanduser(target)))
        if not candidate.is_absolute():
            candidate = profile.parent / candidate
        resolved = candidate.resolve(strict=False)
        resolved_key = str(resolved)
        if resolved_key in by_resolved_path:
            existing = by_resolved_path[resolved_key]
            if label.strip() not in existing["labels"]:
                existing["labels"].append(label.strip())
            if target not in existing["targets"]:
                existing["targets"].append(target)
            continue
        record: dict[str, Any] = {
            "labels": [label.strip()],
            "targets": [target],
            "resolved_path": resolved_key,
            "status": "available" if resolved.is_file() else "missing",
        }
        if resolved.is_file():
            try:
                record.update({key: value for key, value in file_record(resolved).items() if key != "path"})
                record["access"] = "direct"
            except OSError:
                record["status"] = "unreadable"
        records.append(record)
        by_resolved_path[resolved_key] = record
    return records


def inspect_profile(path: Path) -> dict[str, Any]:
    """Report context and gaps without approval promotion or sidecar writes."""
    validation, text, _ = validate_profile(path)
    return {
        "schema_version": 1,
        "found": True,
        "read_only": True,
        "sidecar_path": None,
        "profile": file_record(path),
        "validation": validation,
        "context_status": "approved_complete" if validation["valid"] else "needs_review",
        "authorities": authority_records(path, text),
        "facts_verified": False,
    }


def resolve_profile(path: Path, sidecar: Path | None = None, write_sidecar: bool = True) -> dict[str, Any]:
    validation, text, _ = validate_profile(path)
    if not validation["valid"]:
        raise ProfileError("; ".join(validation["errors"]))
    authorities = authority_records(path, text)
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": file_record(path),
        "validation": validation,
        "authorities": authorities,
        "authority_summary": {
            "total": len(authorities),
            "available": sum(item["status"] == "available" for item in authorities),
            "missing": sum(item["status"] == "missing" for item in authorities),
            **({"unreadable": sum(item["status"] == "unreadable" for item in authorities)}
               if any(item["status"] == "unreadable" for item in authorities) else {}),
        },
        "authority_access": "direct",
    }
    destination = sidecar or path.parent / ".hormozi" / "business.json"
    if write_sidecar:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=destination.parent, prefix="business-", suffix=".tmp", delete=False
        ) as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            temporary = Path(handle.name)
        os.replace(temporary, destination)
        payload["sidecar_path"] = str(destination.resolve())
    else:
        payload["sidecar_path"] = None
        payload["read_only"] = True
    return payload


def profile_from_args(args: argparse.Namespace) -> Path:
    if getattr(args, "profile", None):
        return Path(args.profile).expanduser().resolve()
    found = find_profile(Path(getattr(args, "start", ".")))
    if found is None:
        raise ProfileError("no BUSINESS.md found from start path or its parents")
    return found


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    find = subparsers.add_parser("find", help="find the nearest BUSINESS.md")
    find.add_argument("--start", default=".")
    for name in ("inspect", "validate", "resolve"):
        command = subparsers.add_parser(name)
        command.add_argument("--profile")
        command.add_argument("--start", default=".")
        if name == "resolve":
            command.add_argument("--sidecar")
            command.add_argument("--no-write", action="store_true", help="validate and resolve without writing the sidecar")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "find":
            path = find_profile(Path(args.start))
            if path is None:
                raise ProfileError("no BUSINESS.md found from start path or its parents")
            result: dict[str, Any] = {"found": True, "profile_path": str(path)}
        elif args.command == "inspect":
            path = (Path(args.profile).expanduser().resolve() if args.profile
                    else find_profile(Path(args.start)))
            result = inspect_profile(path) if path is not None else {
                "schema_version": 1,
                "found": False,
                "context_status": "missing",
                "read_only": True,
                "sidecar_path": None,
                "facts_verified": False,
            }
        elif args.command == "validate":
            path = profile_from_args(args)
            validation, _, _ = validate_profile(path)
            result = {"profile_path": str(path), **validation}
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if validation["valid"] else 2
        else:
            path = profile_from_args(args)
            result = resolve_profile(
                path,
                Path(args.sidecar).expanduser().resolve() if args.sidecar else None,
                write_sidecar=not args.no_write,
            )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, UnicodeError, ProfileError) as error:
        print(json.dumps({"error": str(error), "ok": False}, indent=2, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
