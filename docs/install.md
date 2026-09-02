# Install And Migration

## Codex Or Agent Skills Directory

Install only the consolidated folder:

```bash
ln -s /absolute/path/to/hormozi-skills/skills/hormozi /absolute/path/to/skills/hormozi
```

Copying the directory also works. A symlink is easier to keep current during development.

## Supported Runtime Matrix

- **Codex:** supported through a link or copy at `.agents/skills/hormozi`. Verify that the path resolves and run the package validation commands below.
- **Claude Code:** the same canonical folder can be linked at `.claude/skills/hormozi`. Filesystem discovery is supported; model execution still depends on the caller's authentication and compatible Claude installation.
- **OpenClaw:** not supported by version 2. Do not install an OpenClaw link. Support requires a dedicated installer, a valid runtime configuration, and an invocation smoke test before this matrix may change.

Do not create runtime-specific copies of the doctrine or advisor logic. A runtime not listed as supported must fail by absence, not through a dangling or duplicate skill link.

## Business Setup

Copy `skills/hormozi/assets/business-profile-template.md` into the root of the business workspace as `BUSINESS.md`. Complete and review it before setting `Status: approved`.

The profile should link volatile details to current local authorities. Do not put credentials, protected customer data, or full operational exports in it.

Validate it:

```bash
python3 /path/to/hormozi/scripts/business_context.py validate --profile /path/to/BUSINESS.md
```

## Migrating From Version 1

Version 1 installed a router plus fourteen `hormozi-*` child directories. Version 2 has one advisor package.

Early version 2 builds used the name `hormoziskills`. Replace that folder, path, and `$hormoziskills` call with `hormozi`, `skills/hormozi`, and `$hormozi`.

1. Snapshot or preserve the current installed skill directory.
2. Install `hormozi` version 2.
3. Remove the fourteen old child links or copies only after the new install validates.
4. Search local prompts and docs for direct child invocations such as `/hormozi-offers`.
5. Replace them with `$hormozi` and state the requested outcome directly.
6. Validate an approved business profile and run smoke consultations before ending the rollback window.

There are no permanent aliases. Failing clearly is safer than silently routing an old command to behavior the operator did not inspect.

Use the migration diagnostic to get an actionable replacement or scan a workspace before removing old links:

```bash
python3 /path/to/hormozi/scripts/migration_check.py --query "/hormozi-offers"
python3 /path/to/hormozi/scripts/migration_check.py --root /path/to/business-workspace
```

## Bundled Corpus

The optional corpus helper imports plain-text equivalents from material you own or are authorized to use. A JSONL manifest is recommended because it makes licensing and source keys explicit.

```json
{"source_key":"example-book","title":"Example Book","text_path":"example-book/pages.md","locator_prefix":"source:example-book","license_status":"owned"}
```

The full working library ships at `skills/hormozi/private-corpus/`. Store the index at `private-corpus/index/hormozi.sqlite`, file sources under `private-corpus/files/`, and video research under `private-corpus/youtube/`. The skill finds this library from any working directory. An explicit `HORMOZI_CORPUS_ROOT` or a nearby `.hormozi/corpus.json` can still select a different corpus.

The skill-local `private-corpus/` folder is the one home for originals, text, media, page images, source records, and the search index. Git tracks the whole folder with the skill.

The importer enforces the shipped row schema and requires every resolved `text_path` to remain inside `--source-root`, including through symlinks. Retrieval reports when a query is reduced to its twenty-term search bound.

## Verification

Run doctrine validation, the unit tests, the official skill validator for the skill directory, and a clean-install smoke test. Check the full corpus index after each source update.
