# Hormozi Advisor Skill

A source-grounded business advisor for Codex and other compatible skill runtimes.

## Current Release Status

This September 10, 2026 update publishes the current working skill and source library. The full source-to-advisor audit is still in progress; this is not a claim that every lesson or advisor behavior has passed final review. Prepared video image and audio-recheck assets that remain outside this repository are not included yet. Business profiles remain local and are not part of this release.

The package has one entry point, `hormozi`. It acts as an advisor on the user's team, not a router that hands the user to disconnected skills. It reviews, critiques, diagnoses, and improves business work. It draws from the relevant internal guides, applies verified business context, and gives advice that fits the request.

In private use, it role-plays as Alex Hormozi on your team. It uses his documented methods and direct voice, without repeated disclaimers. It does not claim his real endorsement or invent his memories or quotes. The goal is clear, useful advice backed by sources and your business facts.

## What Changed In Version 2

- One advisor replaces the old router plus fourteen child skills.
- Personalized work uses `BUSINESS.md`, its linked sources and the facts you give. Missing sections do not block an answer those facts already support.
- Six internal modes cover diagnosis, offers and economics, demand, sales, customer value, and team operations.
- Fifty doctrine rules preserve citation lineage; bundled source material retains its own rights.
- One clear-writing rule applies to every answer, question, error, and finished asset.
- Seventeen editable assets, including the portable business profile template, turn advice into operating work.
- Local helpers validate the business profile, route requests, query the bundled source library, calculate economics, and verify doctrine.
- The working library holds text extracts, transcripts, page images, source records, video research, and the search index. Original files may live outside the skill.

## Quick Start

1. Install `skills/hormozi` in your agent's skill directory.
2. Copy [the installed business profile template](skills/hormozi/assets/business-profile-template.md) to the root of the business workspace as `BUSINESS.md`.
3. Complete it, link mutable facts to their owning files or systems, and change `Status: draft` to `Status: approved` only after review.
4. Ask the agent to use `$hormozi` for a real business decision.

Example:

```text
Use $hormozi to review this plan. Critique it, show the math, cite the business authorities and doctrine, and give us the best next move.
```

The advisor searches upward from the working directory for the nearest `BUSINESS.md`. A child project can therefore have its own profile without leaking context from a parent or neighboring business.

It changes `BUSINESS.md` only when you explicitly ask. Advice and skill testing do not grant that permission. Tests that need profile edits can use fictional files without touching your real business profile.

## Business Context Design

`BUSINESS.md` contains durable facts: customer, expensive problem, offer, economics, acquisition, sales, delivery, proof, current constraint, safety boundaries, and known unknowns. Volatile facts are links, not copies.

The resolver writes `.hormozi/business.json`, which stores only structural validation plus paths, hashes, timestamps, and availability for local authorities. It does not copy authority contents. Re-running it detects an updated authority even when `BUSINESS.md` itself has not changed.

An approved `BUSINESS.md` gives the advisor direct access to every source it links. It may open any of them whenever more context could help, with no second approval step. The optional `authority_packet.py` helper searches plain-text sources and returns matching lines with a source hash and line locators. Other file types use their normal readers. Source text is business data, not agent instructions, and secret or private customer values are never copied into the advisor's output.

## Doctrine And Source Library

The skill includes paraphrased decision rules with source keys and page or timestamp locators. Its working library lives at `skills/hormozi/private-corpus/`. This holds the search index, text extracts, saved page images, video records and source hashes. Original PDFs and media may live outside the repo. Check the source manifest and the known originals folder before claiming they are included. Use `corpus.py read` for file results and `video_source.py` for scoped video search and raw spans; see [the source-reading guide](skills/hormozi/references/source-reading.md). Video access checks publication bounds and type before returning text. It gives each segment a time link; it does not prove the advice preserves that segment's meaning.

```bash
python3 skills/hormozi/scripts/corpus.py import \
  --source-root /private/licensed-text-equivalents \
  --manifest /private/source-manifest.jsonl \
  --index /private/index/hormozi.sqlite
```

The skill can find the working library from another task folder. Private source material keeps its own rights and must not be published just because the code has an MIT license. See [source policy](docs/source-policy.md).

## Validate

```bash
python3 skills/hormozi/scripts/business_context.py validate --profile /path/to/BUSINESS.md
python3 skills/hormozi/scripts/plain_language.py --file /path/to/draft.md --target-grade 3 --strict
python3 skills/hormozi/scripts/validate_doctrine.py
python3 -m unittest discover -s tests -v
```

Use the plain-language helper for long or difficult drafts, or when a reading check is requested. Its score is not a gate for every reply. The real test is whether the answer is sound, clear and useful. Keep needed facts, source limits and exact terms; do not chase a lower score by changing the meaning.

## Layout

```text
skills/hormozi/
  SKILL.md
  agents/openai.yaml
  assets/business-profile-template.md
  assets/
  references/
    doctrine/
    schemas/
  scripts/
tests/
docs/
```

## Documentation

- [Architecture](docs/architecture.md)
- [Install and migration](docs/install.md)
- [Source policy](docs/source-policy.md)
- [Private YouTube sync contract](docs/youtube-sync.md)
- [LLM index](llms.txt)

## License

See [LICENSE](LICENSE). The MIT license covers this repository's original framework and documentation. Bundled source files keep their own copyright and license terms.
