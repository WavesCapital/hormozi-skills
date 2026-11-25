#!/usr/bin/env python3
"""Add approved, publicly downloadable source files to the bundled private corpus.

Reads a JSON spec (list of objects) and, for each entry, copies the original into
``private-corpus/files/originals/<bundled_original>``, writes per-page records,
appends the file manifest and chunk list, and inserts the chunks into the search
index. Re-running with the same spec skips sources that are already present.

Spec fields per entry: ``path`` (local file), ``bundled_original`` (relative path
under originals), ``slug``, ``title``, ``category``, ``canonical_url``,
``baseline_owner``. PDFs are split with ``pdftotext``; ``.txt`` and ``.md`` files become
one record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import subprocess
from pathlib import Path

from corpus import chunks as split_chunks

SCHEMA = "1.0.0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def pdf_pages(path: Path) -> list[str]:
    info = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, check=True).stdout
    count = int(next(line.split()[-1] for line in info.splitlines() if line.startswith("Pages:")))
    pages = []
    for page in range(1, count + 1):
        text = subprocess.run(["pdftotext", "-f", str(page), "-l", str(page), str(path), "-"],
                              capture_output=True, text=True, check=True).stdout
        pages.append(text.replace("\f", "").strip())
    return pages


def add(skill_root: Path, spec: list[dict]) -> dict:
    files_root = skill_root / "private-corpus" / "files"
    manifest_path = files_root / "file-source-manifest.jsonl"
    chunks_path = files_root / "chunks.jsonl"
    index_path = skill_root / "private-corpus" / "index" / "hormozi.sqlite"
    existing = {json.loads(line)["source_id"].split(":")[0] for line in manifest_path.read_text().splitlines() if line}
    added, chunk_total = [], 0
    connection = sqlite3.connect(index_path)
    for entry in spec:
        source = Path(entry["path"])
        if entry["slug"] in existing:
            continue
        digest = sha256(source)
        source_id = f"{entry['slug']}:{digest[:12]}"
        record_dir = f"{entry['slug']}-{digest[:12]}"
        original = files_root / "originals" / entry["bundled_original"]
        original.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, original)
        fmt = source.suffix.lower().lstrip(".")
        pages = pdf_pages(source) if fmt == "pdf" else [source.read_text(encoding="utf-8-sig").strip()]
        source_path = f"$HORMOZI_CORPUS/files/originals/{entry['bundled_original']}"
        citation_base = {"original_sha256": digest, "source_id": source_id}
        records, chunk_rows = [], []
        empty = 0
        for number, text in enumerate(pages, start=1):
            locator = f"file:{source_id}:p{number:04d}"
            words = len(text.split())
            empty += words == 0
            records.append({
                "citation": {**citation_base, "page": number}, "derived_pdf": None,
                "embedded_text": text, "embedded_word_count": words, "format": fmt,
                "locator": locator, "ocr_error": None, "ocr_status": "not_needed", "ocr_text": "",
                "ocr_word_count": 0, "page": number, "page_image": None, "page_image_sha256": None,
                "schema_version": SCHEMA, "search_text": text, "source_id": source_id,
                "source_path": source_path, "source_sha256": digest,
                "text_quality": "text_ok" if words else "empty",
                "visual_dependency": fmt == "pdf", "visual_review_status": "not_reviewed",
            })
            for chunk_index, content in split_chunks(text) if text else []:
                chunk_id = f"{locator}:c{chunk_index + 1:03d}"
                chunk_rows.append({
                    "canonical_chunk_id": chunk_id, "chunk_id": chunk_id,
                    "citation": {**citation_base, "page": number},
                    "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
                    "is_duplicate": False, "locator": locator, "page": number, "page_image": None,
                    "schema_version": SCHEMA, "section": None, "source_id": source_id,
                    "source_sha256": digest, "text": content, "visual_dependency": fmt == "pdf",
                })
        (files_root / "derived" / "records" / record_dir).mkdir(parents=True, exist_ok=True)
        (files_root / "derived" / "records" / record_dir / "pages.jsonl").write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in records))
        manifest_row = {
            "baseline_owner": entry["baseline_owner"], "bundled_original": entry["bundled_original"],
            "bytes": source.stat().st_size, "canonical_url": entry["canonical_url"],
            "category": entry["category"], "extension": source.suffix.lower(),
            "private_records": f"derived/records/{record_dir}/pages.jsonl",
            "processing": {"conversion": None, "ocr_attempted_count": 0, "ocr_failed_count": 0,
                           "page_count": len(pages), "rendered_page_count": 0,
                           "status": "ok" if not empty else "ok_with_empty_pages",
                           "unresolved_empty_page_count": empty},
            "record_count": len(records), "relative_path": entry["title"],
            "rights": "public_download_review_required", "schema_version": SCHEMA,
            "sha256": digest, "source_id": source_id, "source_path": source_path, "source_type": "file",
        }
        with manifest_path.open("a") as handle:
            handle.write(json.dumps(manifest_row, sort_keys=True) + "\n")
        with chunks_path.open("a") as handle:
            handle.writelines(json.dumps(row, sort_keys=True) + "\n" for row in chunk_rows)
        with connection:
            for row in chunk_rows:
                provenance = {"citation": row["citation"], "page_image": None,
                              "source_sha256": digest, "visual_dependency": row["visual_dependency"],
                              "canonical_url": entry["canonical_url"]}
                cursor = connection.execute(
                    "INSERT INTO chunks(chunk_id, source_type, source_id, title, locator, text, topics, "
                    "published_at, eligibility, canonical_url, provenance_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (row["chunk_id"], "file", source_id, source_id, row["locator"], row["text"], "",
                     None, "private_supplied_source", entry["canonical_url"], json.dumps(provenance, sort_keys=True)))
                connection.execute("INSERT INTO chunks_fts(rowid, title, text, topics) VALUES (?,?,?,?)",
                                   (cursor.lastrowid, source_id, row["text"], ""))
        added.append({"source_id": source_id, "pages": len(pages), "chunks": len(chunk_rows)})
        chunk_total += len(chunk_rows)
    with connection:
        counts = dict(connection.execute(
            "SELECT source_type, COUNT(*) FROM chunks GROUP BY source_type").fetchall())
        connection.execute("INSERT OR REPLACE INTO metadata VALUES ('counts', ?)", (json.dumps(counts, sort_keys=True),))
    connection.close()
    report_path = files_root / "run-report.json"
    report = json.loads(report_path.read_text())
    manifest_lines = [line for line in manifest_path.read_text().splitlines() if line]
    report["counts"]["chunk_count"] += chunk_total
    report["counts"]["processed_source_count"] = len(manifest_lines)
    report["counts"]["verified_file_source_count"] = len(manifest_lines)
    report["counts"]["page_or_section_record_count"] += sum(item["pages"] for item in added)
    report["lineage"]["chunks_sha256"] = sha256(chunks_path)
    report["lineage"]["manifest_sha256"] = sha256(manifest_path)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return {"ok": True, "added": added, "chunks": chunk_total}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--skill-root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    spec = json.loads(Path(args.spec).read_text())
    print(json.dumps(add(Path(args.skill_root).resolve(), spec), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
