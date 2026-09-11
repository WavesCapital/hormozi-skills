#!/usr/bin/env python3
"""Flag possible prose problems; a reading score does not assess meaning or voice."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


JARGON: dict[str, str] = {
    "binding constraint": "main problem",
    "commercial validation": "proof that buyers will pay and use it",
    "constraint call": "main problem",
    "downstream outcome": "later result",
    "downstream result": "later result",
    "evidence-based": "backed by proof",
    "graduation condition": "what must happen before moving on",
    "graduation rule": "what must happen before moving on",
    "intervention": "test or change",
    "mechanism": "how it works",
    "monetization": "how the business makes money",
    "near-term objective": "next goal",
    "near-term outcome": "next result",
    "operating machinery": "how the business works",
    "operating stage": "business stage",
    "original synthesis": "my view based on the sources",
    "prescription": "what to do",
    "priority segment": "main customer group",
    "rejected alternatives": "what not to do yet",
    "sufficiently": "enough",
    "throughput": "total output",
    "unit economics": "money made and spent per customer",
}

FILLER_WORDS = {"actually", "basically", "literally", "really", "super", "very"}
PASSIVE_RE = re.compile(
    r"\b(?:am|are|be|been|being|is|was|were)\s+(?:\w+ly\s+)?\w+(?:ed|en)\b",
    re.IGNORECASE,
)
WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
URL_RE = re.compile(r"https?://\S+")
INLINE_CODE_RE = re.compile(r"`[^`]+`")
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
CITATION_LINE_RE = re.compile(r"^\s*\[(?:HZ-|Business\b|Source\b)", re.IGNORECASE)
GROUPED_NUMBER_RE = re.compile(r"(?<![\w,])[-+]?\d{1,3}(?:,\d{3})+(?:\.\d+)?(?!\w|,\d)")


def visible_prose(markdown: str, ignored_terms: list[str] | None = None) -> str:
    """Return the prose a reader must understand, without code or locators."""

    text = FENCE_RE.sub(" ", markdown)
    text = INLINE_CODE_RE.sub(" ", text)
    text = LINK_RE.sub(r"\1", text)
    text = URL_RE.sub(" ", text)
    kept: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            kept.append("")
            continue
        if CITATION_LINE_RE.match(stripped):
            continue
        if stripped.startswith("Doctrine lineage:"):
            continue
        if re.fullmatch(r"\|?(?:\s*:?-+:?\s*\|)+", stripped):
            continue
        separate_block = bool(re.match(r"^\s{0,3}(?:#{1,6}\s|[-*+]\s+|\d+[.)]\s+|\|)", line))
        line = re.sub(r"^\s{0,3}(?:#{1,6}|[-*+]\s+|\d+[.)]\s+)", "", line)
        line = line.replace("|", ". ")
        if separate_block:
            kept.append("")
        kept.append(line)
        if separate_block:
            kept.append("")
    text = "\n".join(kept)
    for term in ignored_terms or []:
        text = re.sub(re.escape(term), "item", text, flags=re.IGNORECASE)
    return re.sub(r"[ \t]+", " ", text).strip()


def words_in(text: str) -> list[str]:
    return WORD_RE.findall(text)


def sentence_list(text: str) -> list[str]:
    # Markdown soft wraps are not new sentences. Keep paragraphs and list items
    # distinct, but do not let line wrapping make identical prose score easier.
    parts = re.split(r"(?<=[.!?])\s+|\n\s*\n", text)
    return [" ".join(part.strip(" -\t").split()) for part in parts if words_in(part)]


def syllables(word: str) -> int:
    """Return a stable English syllable estimate for readability checks."""

    token = re.sub(r"[^a-z]", "", word.lower())
    if len(token) <= 3:
        return 1
    groups = re.findall(r"[aeiouy]+", token)
    count = len(groups)
    if token.endswith("e") and not token.endswith(("le", "ye")) and count > 1:
        count -= 1
    if token.endswith("es") and len(token) > 4 and not token.endswith(("aes", "ees", "oes")) and count > 1:
        count -= 1
    return max(1, count)


def analyze(
    markdown: str,
    *,
    target_grade: float = 3.0,
    max_sentence_words: int = 16,
    ignored_terms: list[str] | None = None,
) -> dict[str, Any]:
    prose = visible_prose(markdown, ignored_terms)
    sentences = sentence_list(prose)
    words = words_in(prose)
    word_count = len(words)
    sentence_count = max(1, len(sentences))
    syllable_count = sum(syllables(word) for word in words)
    grade = 0.0
    if word_count:
        grade = 0.39 * (word_count / sentence_count) + 11.8 * (syllable_count / word_count) - 15.59
    grade = round(max(0.0, grade), 2)

    long_sentences = [
        {"words": len(words_in(sentence)), "text": sentence[:240]}
        for sentence in sentences
        if len(words_in(sentence)) > max_sentence_words
    ]
    # Thousands separators are part of exact numbers, not extra sentence clauses.
    # Use a counting copy only; keep the original prose in all output and checks.
    multi_comma_sentences = [
        sentence[:240] for sentence in sentences
        if GROUPED_NUMBER_RE.sub(lambda match: match[0].replace(",", ""), sentence).count(",") > 1
    ]
    passive_voice = [sentence[:240] for sentence in sentences if PASSIVE_RE.search(sentence)]
    lower = prose.lower()
    jargon = [
        {"term": term, "try": replacement}
        for term, replacement in JARGON.items()
        if re.search(rf"\b{re.escape(term)}\b", lower)
    ]
    filler = sorted({word.lower() for word in words if word.lower() in FILLER_WORDS})

    issues: list[str] = []
    if not word_count:
        issues.append("no_prose")
    if grade > target_grade:
        issues.append("reading_grade")
    if long_sentences:
        issues.append("long_sentences")
    if multi_comma_sentences:
        issues.append("too_many_commas")
    if passive_voice:
        issues.append("passive_voice")
    if jargon:
        issues.append("jargon")
    if filler:
        issues.append("filler_words")

    return {
        # Bind this result to the complete input before exclusions or cleanup.
        # Readability counts alone cannot prove which final draft was checked.
        "checked_text_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        "ok": not issues,
        "quality_status": "not_assessed",
        "has_review_hints": bool(issues),
        "review_hints": issues,
        "mechanical_status": "flags_to_review" if issues else "no_flags",
        "metric_scope": "Heuristic flags only; not a grade of source fidelity, meaning, natural voice or usefulness.",
        "target_grade": target_grade,
        "reading_grade_estimate": grade,
        "words": word_count,
        "sentences": len(sentences),
        "average_sentence_words": round(word_count / sentence_count, 2),
        "issues": issues,
        "long_sentences": long_sentences,
        "multi_comma_sentences": multi_comma_sentences,
        "passive_voice": passive_voice,
        "jargon": jargon,
        "filler_words": filler,
        "note": "Review each flag. Fix unclear prose, not a number at the cost of meaning. Sentence length, commas and passive-voice matches can be false positives. Read the exact final aloud and check its facts and sources after edits.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--file", type=Path)
    source.add_argument("--text")
    parser.add_argument("--target-grade", type=float, default=3.0)
    parser.add_argument("--max-sentence-words", type=int, default=16)
    parser.add_argument("--ignore-term", action="append", default=[])
    parser.add_argument("--strict", action="store_true", help="exit nonzero when the check finds an issue")
    args = parser.parse_args()

    if args.file:
        markdown = args.file.read_text(encoding="utf-8")
    elif args.text is not None:
        markdown = args.text
    else:
        markdown = sys.stdin.read()

    result = analyze(
        markdown,
        target_grade=args.target_grade,
        max_sentence_words=args.max_sentence_words,
        ignored_terms=args.ignore_term,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2 if args.strict and not result["ok"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
