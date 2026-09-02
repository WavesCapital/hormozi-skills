# YouTube Sync Contract

The package defines how to keep recent public-video evidence current. It ships the current raw responses, transcript bodies, review state, and search data inside the bundled corpus. It does not ship API credentials or a preconfigured channel runner.

## Deployment Responsibilities

A private sync must:

- verify the official channel ID before ingestion;
- inventory regular videos, Shorts, and completed live/VOD items independently;
- exhaust continuation tokens for a frozen or rolling time window and deduplicate by stable video ID;
- preserve exact publication time, canonical URL, item type, metadata hash, chapters when available, timestamped caption provenance, transcript status, speaker-confidence state, visual-dependency state, and duplicate or clip lineage;
- retain immutable dated snapshots while maintaining a separate rolling active view;
- fetch full metadata and transcripts only for new, changed, incomplete, or explicitly repaired items during bounded incremental runs;
- checkpoint resumable work, prove no-change state hashes, stage mutations, verify lineage and leakage, and promote all mutable surfaces atomically;
- run a full rolling-window reconciliation at least every seven days;
- keep uncertain attribution, missing visuals, malformed captions, conflicts, and doctrine changes in explicit review states instead of silently promoting them; and
- keep all raw payloads and transcript text inside the bundled corpus.

The runner and scheduler are deployment-owned because credentials, channel configuration, and automation runtimes vary by install. A deployment may use ScrapeCLI or another audited adapter only when it provides complete, structured, resumable evidence for this contract.

## Corpus Handoff

The sync writes normalized, source-addressed records and rebuilds the bundled retrieval index. The advisor uses the skill-local corpus by default. `HORMOZI_CORPUS_ROOT` or the nearest `.hormozi/corpus.json` can select another corpus.

Query primary file doctrine separately from recent-video evidence:

```bash
python3 skills/hormozi/scripts/corpus.py query \
  --corpus-root skills/hormozi/private-corpus \
  --query "decision-specific terms" \
  --source-type file \
  --limit 6

python3 skills/hormozi/scripts/corpus.py query \
  --corpus-root skills/hormozi/private-corpus \
  --query "recent refinement terms" \
  --source-type youtube \
  --limit 6
```

YouTube evidence does not become canonical doctrine merely because it is recent. A material rule change requires direct attribution, exact timestamp review, conflict review, visual-context review when needed, and an explicit dated evidence decision.
