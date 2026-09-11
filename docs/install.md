# Set up Hormozi Advisor in Codex

This guide is for the agent doing the setup. The owner can start with the prompt in [README.md](../README.md).

## 1. Check the request and the machine

An install/setup request authorizes this local setup, not outreach, business approval, account connections or scheduled work. If the user only asks what the repo does, explain it without installing.

Use the receiving user's paths. Do not reuse paths, business facts or credentials from repository history or test receipts. If the business folder is not clear, ask before saving business context. Do not use the skill checkout as the business workspace.

Check for an existing enabled `hormozi` skill first. Reuse a working install; do not create a second copy with the same name. If a destination exists, inspect it before making changes. Preserve local edits and broken-link evidence; never force-overwrite or delete it.

The bundled command-line helpers use Python 3.10+ and its standard library, including SQLite with FTS5. Use the runtime's available Python command; examples below use `python3`. Git is needed for the Git install method. Extra tools for audio, OCR or new source ingestion are not needed for basic setup. Do not install those or run the full corpus audit as an onboarding step.

The complete tracked source library was about 2.4 GB on September 11, 2026. Check free disk space for the download, temporary checkout and installed copy. Do not silently omit the library to make setup look complete.

## 2. Install the one skill

Read the active bundled `$skill-installer` instructions. Find its actual `scripts/install-skill-from-github.py`; do not guess its location or install the system skill again.

Use these exact repository settings:

- Repository: `WavesCapital/hormozi-skills`
- Branch: `main`
- Skill path: `skills/hormozi`
- Skill name: `hormozi`
- Direct package link: https://github.com/WavesCapital/hormozi-skills/tree/main/skills/hormozi

For a new user-wide install, use the user's `.agents/skills` directory. For an explicitly project-only install, use that business repository's `.agents/skills`. Do not install into both. Follow an explicit user choice or reuse an existing supported installation.

Example for macOS/Linux: set `HORMOZI_INSTALLER` to the actual bundled installer script path discovered above, then run:

```bash
python3 "$HORMOZI_INSTALLER" \
  --repo WavesCapital/hormozi-skills \
  --path skills/hormozi \
  --ref main \
  --dest "$HOME/.agents/skills" \
  --method git
```

On Windows, resolve the user's home directory and use the equivalent absolute destination and Python invocation. Do not paste a macOS path.

The explicit destination avoids depending on the installer's default, which can be `$CODEX_HOME/skills` or `~/.codex/skills`. Keep a working install in those locations rather than duplicating it. The official installer supports GitHub URLs too; the repo/path form above makes the package boundary clear.

Use normal scoped tool approvals if required by that Codex environment. Never bypass them. If Git is unavailable, the installer's download method is an alternative; the full archive still needs disk space. Stop on a real download/access error and report it. A partial copy is not an install.

The installed root must contain `SKILL.md`, `agents/`, `references/`, `scripts/`, `assets/` and `private-corpus/`. Do not install the repository root or just the entrypoint.

[OpenAI's skill documentation](https://learn.chatgpt.com/docs/build-skills) describes user/project discovery, symlink support and installation from other repositories. Local-folder installation is the route for this package; it is not a marketplace plugin or a hosted service.

### If the bundled installer is unavailable

Use a separate checkout only when normal Git access is available. Choose a new local directory, clone this repo's `main` branch, and copy `skills/hormozi` to the selected discoverable skill directory. On systems with symlink support, a link to that complete folder also works and avoids a second source-library copy.

Keep the checkout separate from the business folder. Never replace an existing directory or link without checking it and getting any needed permission. Do not change unrelated Codex configuration. Run the same checks below and report which method and path were used.

## 3. Prove the installed copy works

Set `HORMOZI_SKILL_DIR` to the actual installed folder, not the maintainer's checkout. Run from a separate empty working folder so nearby business/corpus settings cannot hide an install problem:

```bash
python3 "$HORMOZI_SKILL_DIR/scripts/validate_doctrine.py"
python3 "$HORMOZI_SKILL_DIR/scripts/corpus.py" locate --start .
python3 "$HORMOZI_SKILL_DIR/scripts/corpus.py" verify \
  --index "$HORMOZI_SKILL_DIR/private-corpus/index/hormozi.sqlite"
python3 "$HORMOZI_SKILL_DIR/scripts/corpus.py" query \
  --corpus-root "$HORMOZI_SKILL_DIR/private-corpus" \
  --source-type file --query "value equation" --limit 1
```

Inspect the outputs, not just the exit codes. Doctrine and index checks must report `ok: true`. Discovery must find the intended installed library. A user's existing `HORMOZI_CORPUS_ROOT` or `.hormozi/corpus.json` can override it; do not alter those settings silently. The explicit-root commands test this install independently.

Open an exact locator returned by the query:

```bash
python3 "$HORMOZI_SKILL_DIR/scripts/corpus.py" read \
  --corpus-root "$HORMOZI_SKILL_DIR/private-corpus" \
  --locator "$HORMOZI_TEST_LOCATOR" --context 0 --max-chars 2000
```

Set `HORMOZI_TEST_LOCATOR` to that real returned value; do not invent a locator. Check that text is returned and local citation/image paths resolve under the new install. A bounded read can be partial; it tests access, not full-source comprehension. Missing originals or video visuals must stay labeled as missing. Do not rebuild the index or rewrite saved source history to hide a gap.

Use the bundled Skill Creator validator on the installed folder when available. Confirm Codex lists `hormozi` once at the intended path with no discovery error. File presence alone does not prove discovery. The skill should be available on the next turn; if it does not appear, restart Codex and check again. Do not claim to have restarted the user's app without doing so.

On that next turn, try:

> Use $hormozi. My fictional shop sells an item for $100. It costs $60 to deliver. What is left before other costs?

The answer should be $40, in plain words, without making a profile or demanding a full audit. If a new turn is needed, give the owner this exact check and label runtime discovery/use pending; do not pretend the smoke test ran.

## 4. Set up the user's business context

Install-only requests stop after verification and an offer to help with context. The README's full setup prompt also asks for business onboarding:

1. Read `references/onboarding.md` and `references/business-context.md` in the installed skill.
2. Use an explicitly selected `BUSINESS.md`; otherwise search upward from the user's business workspace with `business_context.py find --start BUSINESS_FOLDER`. Do not search sibling businesses.
3. If a profile exists, inspect it read-only and ask only for facts needed now. Do not replace it with the template.
4. If there is none, ask a few short questions: “What do you sell? Who buys it? What do you want help with first?” Read authorized existing business files before asking for facts they already contain.
5. Help draft the profile using `assets/business-profile-template.md`. Save it only when asked; the full README setup prompt permits helping draft it, not self-approval. Keep unknown facts unknown and drafts marked draft.
6. Keep the main business facts in the profile. Link changing figures, proof, product docs, meeting history and live systems to their real owners. Do not duplicate them or connect accounts without permission.
7. Review with the user. Set approved status only after their approval. Full-profile `validate` requires approved status and complete required sections; an expected draft validation failure is not an install failure.

Save `BUSINESS.md` in that user's business workspace, outside the installed skill and its repository. Keep it out of public source-control uploads. For separate apps of one business, their project instructions can name the same absolute profile; use `--profile` rather than copying it. Change project instructions only within the user's setup request.

Ordinary advice uses `inspect` and relevant source reads. `inspect --check-authorities` is a full local-link check when wanted. `resolve` creates the optional `.hormozi/business.json` sidecar during authorized setup; it is not required for every answer.

## 5. Hand back a clear result

Tell the user:

- Where the skill is installed and which checks actually passed.
- Whether Codex discovered it and whether an actual invocation ran.
- Whether business context is existing, draft, approved or still needed.
- One useful first prompt, plus any missing source or access limitation.

Do not claim this installs a daily video feed, connects a CRM, sets a model, gives financial guarantees, or finishes the source-by-source audit. Core use needs the user's existing Codex access, not a separate API key. Keep their current model and account settings.

## Update an existing install

Update only when asked. Check whether the install is a copy or a symlink and preserve local edits.

- **Linked checkout:** confirm its remote is this repository and its working tree is clean; then use a fast-forward-only update. Stop on local edits or a divergent branch. Do not reset or force-push.
- **Installed copy:** install the new version into a separate staging directory. Run the checks above. Ask before replacing the existing install if replacement is not already authorized, and retain a recoverable backup. The official installer refuses an existing destination; do not work around that by deleting it blindly.

Keep the business profile outside the replacement. Do not copy another user's profile, credentials, sidecar or scheduled tasks. Recheck discovery after the switch.

## Older installs and other agents

Only `hormozi` is current. `hormoziskills` and the old fourteen `hormozi-*` child skills are retired. Inspect old copies/links, install and verify the current skill, then get permission before removing old copies. Do not remove other skills just because their names look similar.

The same folder can be used in Claude Code's skill directory, but this setup path is tested for Codex. OpenClaw is not supported by this release.

For new sources and optional scheduled ingestion, read [source policy](source-policy.md) and [YouTube sync](youtube-sync.md). Those are separate work, not install steps.

## Setup verification: September 11, 2026

The bundled OpenAI installer downloaded `skills/hormozi` from GitHub `main` with the Git method into a new temporary directory on macOS. The installed skill passed the official skill validator and its doctrine check. Its copied index passed SQLite integrity and matched 13,629 search rows. A bounded file query and read returned text and a hash-checked image path inside the new install, not the author's original checkout.

Codex's native skill listing found the test install enabled through a project-local link. An ephemeral, read-only Astra turn loaded that exact installed entrypoint and answered the $100 minus $60 smoke test correctly: $40. No business profile was created. The repository's 238 tests and the setup docs' local links also passed. This is install/access proof on macOS, not a full source review, a test of every OS, or approval of a real business profile.
