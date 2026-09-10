#!/usr/bin/env python3
"""Return deterministic request-type and operating-mode candidates."""

from __future__ import annotations

import argparse
import json
import re


MODE_TERMS = {
    "diagnose": {
        "constraint": 5, "bottleneck": 5, "audit": 3, "diagnose": 5, "priority": 3,
        "roadmap": 2, "stage": 2, "funnel": 2, "current funnel": 6, "what should": 2,
        "where does scale break": 7, "scale break": 5, "highest-leverage": 4,
        "highest leverage": 4, "next": 1,
    },
    "offer-economics": {
        "offer": 5, "price": 4, "pricing": 4, "margin": 4, "economics": 5, "ltv": 4,
        "cac": 4, "value equation": 5, "guarantee": 3, "payment": 2, "monetize": 3,
    },
    "demand": {
        "lead": 3, "ads": 4, "advertising": 4, "hook": 3, "creative": 3, "campaign": 3,
        "audience": 3, "outbound": 2, "referral": 2, "launch": 4, "traffic": 4, "acquisition": 4,
    },
    "sales": {
        "sales": 4, "close": 4, "closing": 4, "objection": 4, "call": 2, "show rate": 4,
        "pipeline": 3, "follow up": 3, "nurture": 3, "script": 3, "conversion": 3,
        "interested merchant": 4, "interested-to-referral": 7, "provider-ready referral": 6,
        "referral conversion": 5,
    },
    "customer-value": {
        "retention": 5, "churn": 5, "onboarding": 4, "activation": 4, "delivery": 3,
        "upsell": 3, "customer value": 5, "lifetime": 3, "lifetime value": 5, "service": 2,
        "renewal": 4, "live merchant": 5, "first funded": 6, "first transaction": 5,
        "time to value": 5, "repeated use": 6, "repeat use": 6, "expansion": 3,
    },
    "team-operations": {
        "team": 5, "hire": 4, "hiring": 4, "manager": 3, "leadership": 3, "capacity": 3,
        "operations": 4, "process": 2, "quality": 3, "training": 3, "accountability": 3,
        "handoff": 6, "ownership": 4, "operating cadence": 5, "headcount": 5,
    },
}

INSPECTION_TERMS = (
    "skill audit", "audit the skill", "source catalog", "source list", "corpus", "doctrine map",
    "what sources", "citation coverage", "capability audit", "how is the skill",
)
NOT_APPLICABLE_TERMS = (
    "generic marketing plan", "general marketing plan", "generic marketing ideas",
    "general email marketing ideas", "generic email marketing ideas",
)
DISTINCTIVE_DOCTRINE_TERMS = ("value equation",)
BUSINESS_MARKERS = (
    " my ", " our ", " us ", " we ", "this business", "this offer", "this company",
    " co ", " company ", " business ", "for the business", "for my", "for our",
    "improve this", "write this", "build me",
)
GENERIC_EXECUTION_TERMS = (
    "social media calendar", "social calendar", "content calendar", "seo tips", "seo advice",
    "seo roadmap", "technical seo", "search rankings", "organic search",
    "search engine optimization tips", "search engine optimization advice", "blog calendar",
    "generic ad copy", "generic email copy", "keyword strategy",
)
GENERIC_EXECUTION_PATTERNS = (
    re.compile(
        r"(?i)\b(?:backlinks?|keywords?|link[- ]building|on[- ]page|off[- ]page|"
        r"organic search|search|serp|seo)\b"
    ),
)
HORMOZI_LENS_TERMS = (
    "hormozi lens", "hormozi framework", "hormozi doctrine", "according to hormozi",
    "what does hormozi", "using hormozi", "use hormozi", "hormozi school of thought",
    "hormozi prism", "hormozi worldview", "hormozi conceptual guide",
)
HORMOZI_NAME = r"(?:alex\s+)?hormozi"
GENERATION_VERB = r"(?:answer|compose|copy|create|draft|ghostwrite|give|mimic|respond|rewrite|roleplay|sound|speak|use|write)"
STYLE_NOUN = r"(?:persona|style|tone|voice)"
ROLEPLAY_PATTERNS = (
    re.compile(
        rf"(?i)\b(?:act\s+as|be|become|channel|imagine\s+you(?:\s+are|['’]re)|impersonate|"
        rf"pretend(?:\s+to\s+be|\s+you(?:\s+are|['’]re))|role[- ]?play(?:\s+as)?)\b"
        rf".{{0,50}}\b{HORMOZI_NAME}\b"
    ),
    re.compile(
        rf"(?i)\b{GENERATION_VERB}\b.{{0,100}}"
        rf"(?:\b(?:as|like)\b.{{0,30}}\b{HORMOZI_NAME}\b|"
        rf"\b(?:in|with|using)\b.{{0,25}}\b(?:the\s+)?{STYLE_NOUN}\b.{{0,35}}\b(?:of\s+)?{HORMOZI_NAME}\b|"
        rf"\b(?:the\s+)?{STYLE_NOUN}\b.{{0,35}}\b(?:of\s+)?{HORMOZI_NAME}\b|"
        rf"\b{HORMOZI_NAME}(?:['’]s|s')?\b.{{0,35}}\b{STYLE_NOUN}\b|"
        rf"\b(?:the\s+)?way\b.{{0,25}}\b{HORMOZI_NAME}\b.{{0,20}}\b(?:does|speaks|talks|would|writes)\b)"
    ),
    re.compile(
        rf"(?i)\b{HORMOZI_NAME}(?:['’]s|s')?\b.{{0,35}}\b{STYLE_NOUN}\b"
        rf".{{0,100}}\b{GENERATION_VERB}\b"
    ),
)
HORMOZI_LENS_PATTERN = re.compile(
    r"(?i)(?:alex )?hormozi(?:['’]s|s')?\s+"
    r"(?:approach|conceptual\s+guide|doctrine|framework|ideas?|lens|method|methodology|"
    r"model|playbook|principles?|prism|school\s+of\s+thought|system|thinking|worldview)"
)
HORMOZI_MENTION_PATTERN = re.compile(rf"(?i)\b{HORMOZI_NAME}\b")
LENS_CONCEPT_PATTERN = re.compile(
    r"(?i)\b(approach|concepts?|doctrine|framework|heuristics?|ideas?|lens|lessons?|"
    r"conceptual\s+guide|method|methodology|model|perspective|philosophy|playbook|"
    r"principles?|prism|strategy|system|teachings?|thinking|worldview|school\s+of\s+thought)\b"
)
ACCORDING_TO_HORMOZI_PATTERN = re.compile(rf"(?i)\baccording\s+to\s+{HORMOZI_NAME}\b")
HORMOZI_ATTRIBUTION_PATTERN = re.compile(
    rf"(?i)\b(?:according\s+to|based\s+on|following|per|through|under|using|with)\s+"
    rf"(?:the\s+)?{HORMOZI_NAME}\b"
)
HORMOZI_RECOMMENDATION_PATTERN = re.compile(
    rf"(?i)\b(?:what|how)\s+(?:would|does|did)\s+{HORMOZI_NAME}\s+"
    r"(?:advise|approach|recommend|suggest)\b"
)
SKILL_INVOCATION_PATTERN = re.compile(r"(?i)(?:\$|/)hormozi(?![a-z0-9-])")
IMITATION_ACTION_PATTERN = re.compile(
    r"(?i)\b(answer|compose|copy|craft|create|draft|emulate|give|ghostwrite|mimic|perform|"
    r"reply|respond|rewrite|role[- ]?play|sound|speak|talk|use|write)\b"
)
IMITATION_CONNECTOR_PATTERN = re.compile(
    r"(?i)\b(as|like)\b|\b(?:in|using|with)\s+(?:the\s+)?(?:persona|style|tone|voice)\b|"
    r"\bthe\s+way\b"
)
IMITATION_IDENTITY_PATTERN = re.compile(
    r"(?i)\b(act\s+as|be|become|channel|emulate|imagine\s+you(?:\s+are|['’]re)|"
    r"impersonate|perform\s+as|pretend(?:\s+to\s+be|\s+you(?:\s+are|['’]re))|"
    r"role[- ]?play(?:\s+as)?)\b"
)
STYLE_FEATURE_PATTERN = re.compile(r"(?i)\b(cadence|manner|persona|style|tone|voice)\b")
GENERAL_EXPLANATION_PATTERN = re.compile(
    r"(?i)^\s*(?:analyze|define|describe|explain|how (?:did|does|would)|summarize|"
    r"tell me about|what (?:did|does|is|was))\b"
)
def normalize(query: str) -> str:
    return " " + re.sub(r"\s+", " ", query.lower()).strip() + " "


def contains_known_business_name(query: str, business_name: str | None) -> bool:
    if not business_name or not business_name.strip():
        return False
    return bool(re.search(
        rf"(?i)(?<![A-Za-z0-9]){re.escape(business_name.strip())}(?![A-Za-z0-9])",
        query,
    ))


def requests_roleplay(query: str) -> bool:
    if any(pattern.search(query) for pattern in ROLEPLAY_PATTERNS):
        return True
    if not HORMOZI_MENTION_PATTERN.search(query):
        return False
    if GENERAL_EXPLANATION_PATTERN.search(query):
        return False
    return bool(
        IMITATION_IDENTITY_PATTERN.search(query)
        or STYLE_FEATURE_PATTERN.search(query)
        or re.search(r"(?i)^\s*as\s+(?:alex\s+)?hormozi\b", query)
        or re.search(r"(?i)\bthe\s+way\b.{0,50}\b(?:alex\s+)?hormozi\b", query)
        or (
            IMITATION_ACTION_PATTERN.search(query)
            and IMITATION_CONNECTOR_PATTERN.search(query)
        )
        or (
            IMITATION_ACTION_PATTERN.search(query)
            and re.search(r"(?i)\b(persona|style|tone|voice)\b", query)
        )
    )


def classify_request(query: str, business_name: str | None = None) -> str:
    text = normalize(query)
    if any(term in text for term in INSPECTION_TERMS):
        return "inspection"
    has_business_marker = (
        any(marker in text for marker in BUSINESS_MARKERS)
        or contains_known_business_name(query, business_name)
    )
    has_hormozi_mention = bool(HORMOZI_MENTION_PATTERN.search(query))
    has_explicit_skill_invocation = bool(SKILL_INVOCATION_PATTERN.search(query))
    has_business_domain_signal = (
        any(term in text for terms in MODE_TERMS.values() for term in terms)
        or any(term in text for term in GENERIC_EXECUTION_TERMS)
        or any(pattern.search(query) for pattern in GENERIC_EXECUTION_PATTERNS)
        or has_business_marker
    )
    has_hormozi_lens = (
        requests_roleplay(query)
        or any(term in text for term in HORMOZI_LENS_TERMS)
        or bool(HORMOZI_LENS_PATTERN.search(query))
        or bool(ACCORDING_TO_HORMOZI_PATTERN.search(query))
        or bool(HORMOZI_ATTRIBUTION_PATTERN.search(query))
        or bool(HORMOZI_RECOMMENDATION_PATTERN.search(query))
        or (has_explicit_skill_invocation and has_business_domain_signal)
        or (has_hormozi_mention and bool(LENS_CONCEPT_PATTERN.search(query)))
    )
    if any(term in text for term in NOT_APPLICABLE_TERMS) and not has_hormozi_lens:
        return "not_applicable"
    if (
        (any(term in text for term in GENERIC_EXECUTION_TERMS)
        or any(pattern.search(query) for pattern in GENERIC_EXECUTION_PATTERNS))
        and not has_business_marker
        and not has_hormozi_lens
    ):
        return "not_applicable"
    if has_explicit_skill_invocation and not has_business_domain_signal:
        return "not_applicable"
    if has_business_marker:
        return "personalized_consulting"
    if (
        has_hormozi_lens
        or (
            has_hormozi_mention
            and bool(GENERAL_EXPLANATION_PATTERN.search(query))
        )
        or any(term in text for term in DISTINCTIVE_DOCTRINE_TERMS)
        or " hormozi framework" in text
    ):
        return "general_doctrine"
    # Private role-play is allowed. This helper suggests a route; it cannot
    # establish actual identity, endorsement, or the truth of a purported quote.
    # A named request with no business facts can start a general conversation.
    return "general_doctrine" if has_hormozi_mention else "not_applicable"


def route(query: str, business_name: str | None = None) -> dict[str, object]:
    request_type = classify_request(query, business_name)
    if request_type in {"inspection", "not_applicable"}:
        return {
            "request_type": request_type,
            "profile_required": False,
            "business_context_required": False,
            "primary_candidate": None,
            "ambiguous_top_score": False,
            "candidates": [],
            "mode_applicable": False,
            "advisory_only": True,
        }
    text = normalize(query)
    scores = {
        mode: sum(weight for term, weight in terms.items() if term in text)
        for mode, terms in MODE_TERMS.items()
    }
    # A question that explicitly compares multiple remedies and asks which one
    # comes first is a constraint-diagnosis request before it is a mode request.
    # Keep this narrow so ordinary single-mode questions such as "which channel
    # should we scale first?" still route directly to their operating mode.
    if " or " in text and (
        re.search(r"\bfirst\b", text)
        or "highest leverage" in text
        or "highest-leverage" in text
        or "next move" in text
    ):
        scores["diagnose"] += 16
    if not any(scores.values()):
        scores["diagnose"] = 1
    ranked = sorted(scores.items(), key=lambda item: (-item[1], list(MODE_TERMS).index(item[0])))
    candidates = [{"mode": mode, "score": score} for mode, score in ranked if score > 0]
    top_score = candidates[0]["score"]
    ambiguous = len(candidates) > 1 and candidates[1]["score"] == top_score
    return {
        "request_type": request_type,
        "profile_required": False,
        "business_context_required": request_type == "personalized_consulting",
        "primary_candidate": None if ambiguous else candidates[0]["mode"],
        "ambiguous_top_score": ambiguous,
        "candidates": candidates,
        "mode_applicable": True,
        "advisory_only": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument(
        "--business-name",
        help="Exact approved profile business name when the query uses that proper name",
    )
    args = parser.parse_args()
    print(json.dumps(route(args.query, args.business_name), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
