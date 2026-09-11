# September 11, 2026 Astra upgrade

The advisor keeps its source-backed reasoning and plain voice, with less repeated instruction text. This release applies the approved audit of OpenAI's [Astra skills and prompts guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra). It does not complete the separate full-source audit.

## What changed

1. Reduced the entrypoint from 1,829 to 730 words. It states the result and boundaries instead of a long mandatory process.
2. Kept one third-grade writing standard in the entrypoint. Detailed writing help is conditional; source lineage has its own linked file. Removed repeated writing boilerplate from 58 reference/asset files.
3. Made decision checks conditional. A calculation, rewrite, critique and implementation each have a different finish line. Tests and templates are used when they help, not on every reply.
4. Made `business_context.py inspect` lightweight. It reads the profile and lists links without opening all authorities. `--check-authorities` retains the full maintenance check; `resolve` retains authorized sidecar setup.
5. Added the shared Waveforce business-profile pointer to workspace instructions used by attached apps. No duplicate business profiles are needed.
6. Retired the keyword router from normal advisory work. It remains for compatibility; explicit invocation is no longer rejected because a short follow-up lacks business keywords.
7. Kept case-specific teaching, exceptions and citation lineage in source maps instead of inflating the entrypoint.
8. Split file, audio and video reader guidance. Video calls now return a reusable source handle carrying scope and hash pins. Every use still runs the existing integrity, date, Shorts, identity and path checks. Handles contain settings, not source text or authorization.
9. Separated answering from permanent doctrine promotion. A checked passage can support an ordinary answer; adding a lasting rule still needs the promotion review.
10. Made readability results explicitly advisory. Existing `ok` and `--strict` behavior remain for compatibility, but they are mechanical flags, not a quality score.
11. Removed exact-prose/repeated-boilerplate assertions. Kept source integrity, scope, money, packaging, context and no-write checks; added tests for the changed behavior.
12. Added repeatable real Astra cases and saved a paired five-turn run for each version, including a two-turn change of facts.
13. Defined safe persistence: finish authorized implementation and relevant checks, fix in-scope failures, and stop only at a verified result or a specific missing input/access boundary. An audit still grants no implementation or publishing authority.
14. Split the large workspace Goal into its requirements, one resume checkpoint, and a verbatim historical copy. The old Goal text was retained in full; the source-audit requirements remain open.

## Verification

The full repository test suite, doctrine validation, official OpenAI skill validation, local reference checks and changed-file whitespace checks passed. New source-handle checks cover a moved daily pointer, conflicting settings, raw-text tampering, excluded Shorts, malformed handles, metadata-only selection and paged content pins. Context checks prove lightweight inspection avoids authority reads and explicit profiles work from attached repositories without writing files.

The [real-model sample](../evaluations/astra/README.md) used `gpt-6-astra` with confirmed `low` effort for both versions. Both passed the declared copy, arithmetic, evidence-limit and changed-facts checks. The candidate preserved the fee basis and payout trigger, did not promise buyer approval, and changed its diagnosis from low outreach to a 10% call show rate when the facts changed. No real profile/source-body reads, sends or writes occurred in the model tool traces.

Across those five turns, returned instruction text fell from 173,465 to 38,341 characters (about 78%), and read commands fell from 11 to 7. This is observed tool-output size, not measured token savings, latency or a universal quality gain. Entry text fell about 60%. Answers were reviewed by the maintainer, not Kyle or an independent blinded judge.

Both native runs completed all turns. Logs contained state-database lookup fallback warnings and missing shell-snapshot cleanup warnings. No failed advisor read or missing answer was observed. These environment warnings are disclosed; the tests are not a certification of the desktop runtime. Raw logs remain local; the committed receipt retains commands, hashes, answers and native turn IDs without raw environment logs.

## Compatibility and unchanged boundaries

- `inspect` intentionally changes its default `authorities` output to an empty list and adds `authorities_checked: false` plus `authority_links`. Callers that need authority hashes must add `--check-authorities`; the full `resolve` contract is unchanged.
- Source handles do not freeze future user permission. If task bounds narrow, request a fresh handle with the new bounds. A handle cannot replace visual review, source interpretation, paging pins or publication rights.
- The real `BUSINESS.md`, its sidecar, source bodies and daily enrichment schedule/model were not edited by this release. Concurrent September 11 enrichment changes are excluded from this commit.
- The shared installed skill is a symlink to this repository, so it receives the verified changes directly.
- Prepared video media and the full corpus/lesson/held-out advisor audits remain unfinished in the separate Goal. This small Astra regression sample does not close them.
