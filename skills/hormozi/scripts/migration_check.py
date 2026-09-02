#!/usr/bin/env python3
"""Find old Hormozi skill names and return the current invocation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


LEGACY_NAMES = (
    "hormoziskills",
    "hormozi-branding", "hormozi-closing", "hormozi-customer-value", "hormozi-goated-ads",
    "hormozi-hooks", "hormozi-launch-campaigns", "hormozi-lead-nurture", "hormozi-leads",
    "hormozi-money-models", "hormozi-offers", "hormozi-pricing", "hormozi-proof",
    "hormozi-scaling-roadmap", "hormozi-team-scaling",
)
TEXT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".toml"}


def names_in(text: str) -> list[str]:
    return [name for name in LEGACY_NAMES if name in text]


def scan(root: Path, maximum: int = 200) -> list[dict[str, object]]:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError("scan root not found")
    matches = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES or ".git" in path.parts:
            continue
        found = names_in(path.read_text(encoding="utf-8", errors="ignore"))
        if found:
            matches.append({"path": str(path), "legacy_names": found})
        if len(matches) >= maximum:
            break
    return matches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query")
    parser.add_argument("--root")
    args = parser.parse_args()
    try:
        if bool(args.query) == bool(args.root):
            raise ValueError("provide exactly one of --query or --root")
        matches = (
            [{"legacy_names": names_in(args.query)}] if args.query is not None and names_in(args.query)
            else []
        ) if args.query is not None else scan(Path(args.root))
        print(json.dumps({
            "ok": True,
            "matches": matches,
            "replacement": "$hormozi with the requested outcome stated directly",
            "permanent_aliases": False,
        }, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error), "ok": False}, indent=2, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
