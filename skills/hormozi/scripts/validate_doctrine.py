#!/usr/bin/env python3
"""Validate the public doctrine index, citations, mode files, and asset lineage."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


MODES = {"diagnose", "offer-economics", "demand", "sales", "customer-value", "team-operations"}
RULE_RE = re.compile(r"^HZ-(?:DIA|OFE|DEM|SAL|CV|OPS|SYN)-\d{3}$")


def validate(root: Path) -> dict[str, Any]:
    index_path = root / "references" / "doctrine" / "rule-index.json"
    errors: list[str] = []
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {"ok": False, "errors": [f"cannot read doctrine index: {error}"]}
    rules = data.get("material_rules", [])
    ids = [rule.get("rule_id") for rule in rules]
    id_set = set(ids)
    if len(ids) != len(id_set):
        errors.append("rule IDs are not unique")
    if any(not isinstance(rule_id, str) or not RULE_RE.fullmatch(rule_id) for rule_id in ids):
        errors.append("one or more rule IDs have an invalid format")
    if "HZ-SYN-004" not in id_set:
        errors.append("missing global clear-writing rule HZ-SYN-004")
    observed_modes = {rule.get("mode") for rule in rules if rule.get("mode") != "shared"}
    if observed_modes != MODES:
        errors.append(f"mode set mismatch: {sorted(observed_modes)}")
    for mode in MODES:
        if not (root / "references" / "doctrine" / f"{mode}.md").is_file():
            errors.append(f"missing doctrine mode file: {mode}.md")
    for rule in rules:
        rule_id = rule.get("rule_id", "unknown")
        if not str(rule.get("statement", "")).strip() or not rule.get("decision_logic"):
            errors.append(f"{rule_id} lacks a statement or decision logic")
        citations = rule.get("citations", [])
        if not citations:
            errors.append(f"{rule_id} lacks citations")
        for citation in citations:
            if not citation.get("source_key") or not citation.get("locator"):
                errors.append(f"{rule_id} has an incomplete citation")
            if str(citation.get("locator", "")).startswith("youtube:"):
                if not str(citation.get("canonical_url", "")).startswith("https://www.youtube.com/watch"):
                    errors.append(f"{rule_id} has a YouTube citation without a canonical timestamp URL")
                if citation.get("review_status") != "manually_reviewed_for_material_rule":
                    errors.append(f"{rule_id} has an unreviewed YouTube material citation")
        for related in rule.get("related_rule_ids", []):
            if related not in id_set:
                errors.append(f"{rule_id} references unknown related rule {related}")
        for asset in rule.get("asset_consumers", []):
            asset_path = root / "assets" / f"{asset}.md"
            if not asset_path.is_file():
                errors.append(f"{rule_id} references missing asset {asset}")
            elif rule_id not in asset_path.read_text(encoding="utf-8"):
                errors.append(f"asset {asset} omits its declared rule {rule_id}")
    coverage = data.get("asset_rule_coverage", {})
    asset_files = {path.stem for path in (root / "assets").glob("*.md")}
    if set(coverage) != asset_files:
        errors.append("asset coverage keys do not exactly match asset files")
    for asset, covered_ids in coverage.items():
        for rule_id in covered_ids:
            if rule_id not in id_set:
                errors.append(f"asset coverage {asset} references unknown rule {rule_id}")
    # Shared rules belong at the entrypoint; behavioral cases assess actual voice.
    global_style_paths = (root / "SKILL.md",)
    for path in global_style_paths:
        if not path.is_file() or "HZ-SYN-004" not in path.read_text(encoding="utf-8"):
            errors.append(f"global clear-writing rule is not routed through {path.relative_to(root)}")
    concepts = data.get("concepts", [])
    for concept in concepts:
        for rule_id in concept.get("rule_ids", []):
            if rule_id not in id_set:
                errors.append(f"concept {concept.get('concept_id')} references unknown rule {rule_id}")
    return {
        "ok": not errors,
        "errors": sorted(set(errors)),
        "rules": len(rules),
        "modes": sorted(observed_modes),
        "assets": len(asset_files),
        "concepts": len(concepts),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    result = validate(Path(args.skill_root).expanduser().resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
