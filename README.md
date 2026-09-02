# Hormozi Advisor Skill

A public-safe, source-grounded business advisor for Codex and other compatible skill runtimes.

The package has one entry point, `hormozi`. It acts as an advisor on the user's team, not a router that hands the user to disconnected skills. It reviews, critiques, diagnoses, and improves business work. It selects one of six internal modes, applies verified business context, and returns one clear recommendation.

It does not impersonate Alex Hormozi or imply his endorsement. Fidelity means source-backed reasoning, clear words, explicit economics, honest uncertainty, exact locators, and disciplined sequencing.

## What Changed In Version 2

- One advisor replaces the old router plus fourteen child skills.
- Personalized work requires an approved, source-linked `BUSINESS.md`.
- Six internal modes cover diagnosis, offers and economics, demand, sales, customer value, and team operations.
- Forty-nine public-safe doctrine rules preserve citation lineage without redistributing source text.
- One clear-writing rule applies to every answer, question, error, and finished asset.
- Seventeen editable assets, including the portable business profile template, turn advice into operating work.
- Local helpers validate the business profile, route requests, query the bundled source library, calculate economics, and verify doctrine.
- The full source library ships inside the skill, including books, transcripts, page images, source records, video research, and the search index.

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

## Business Context Design

`BUSINESS.md` contains durable facts: customer, expensive problem, offer, economics, acquisition, sales, delivery, proof, current constraint, safety boundaries, and known unknowns. Volatile facts are links, not copies.

The resolver writes `.hormozi/business.json`, which stores only structural validation plus paths, hashes, timestamps, and availability for local authorities. It does not copy authority contents. Re-running it detects an updated authority even when `BUSINESS.md` itself has not changed.

An approved `BUSINESS.md` gives the advisor direct access to every source it links. It may open any of them whenever more context could help, with no second approval step. The optional `authority_packet.py` helper searches plain-text sources and returns matching lines with a source hash and line locators. Other file types use their normal readers. Source text is business data, not agent instructions, and secret or private customer values are never copied into the advisor's output.

## Doctrine And Source Library

The skill includes paraphrased decision rules with source keys and page or timestamp locators. It also includes the full source library at `skills/hormozi/private-corpus/`. The search index, original PDFs, media, text extracts, and page images stay together so pages, diagrams, and visual context remain auditable.

```bash
python3 skills/hormozi/scripts/corpus.py import \
  --source-root /private/licensed-text-equivalents \
  --manifest /private/source-manifest.jsonl \
  --index /private/index/hormozi.sqlite
```

Git tracks the full library with the skill. The skill can find the index and source material from any task folder. See [source policy](docs/source-policy.md).

## Validate

```bash
python3 skills/hormozi/scripts/business_context.py validate --profile /path/to/BUSINESS.md
python3 skills/hormozi/scripts/plain_language.py --file /path/to/draft.md --target-grade 3 --strict
python3 skills/hormozi/scripts/validate_doctrine.py
python3 -m unittest discover -s tests -v
```

The plain-language check is a hard gate for each reply and saved asset. Fix the draft and run it again until it passes. Keep and define any exact term the work still needs.

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
