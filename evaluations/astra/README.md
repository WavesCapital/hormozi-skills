# Astra regression checks

These are small real-model checks, separate from the fast unit tests. They test finished copy, fee/commission math, limited evidence, missing business context, and changed facts in a real two-turn conversation.

Run the same fixtures against a saved pre-change skill and the candidate:

```bash
python3 evaluations/astra/run.py --codex /absolute/path/to/codex \
  --skill /absolute/path/to/saved-skill --output /new/path/baseline
python3 evaluations/astra/run.py --codex /absolute/path/to/codex \
  --skill skills/hormozi --output /new/path/candidate
```

The runner uses Astra, records the effective effort, and requires ephemeral, read-only sessions with network access off and no approvals. Configured connectors, plugins, hooks and memory features are disabled for the subprocess, not the user's app. Real business profiles and source bodies are outside these synthetic cases. The test criteria stay out of the model prompt. Output directories must be new; the runner never overwrites a prior result. Runs use the account's normal model usage.

Grade the actual answers against each case's `checks`. Also read the completed tool events: verify the intended skill was read, unrelated copies and business files were not accessed, and no write or external action occurred. Treat extra claims, lost terms, bad math, an invented source, or wrong permissions as a failure even if the prose sounds good. Fix a real failure and rerun the affected case; repeat the paired set after a material prompt change. Do not change expected results just to make a candidate pass.

For voice, read it out loud: simple words, complete thoughts, clear next move, honest limits, and no unnecessary lecture. Reading-grade hints do not prove quality. Private consulting may use the agreed role-play; customer copy must use the real sender's voice.

The September 11 [saved answers and receipts](results/2026-09-11.json) are a maintainer-reviewed, non-blind sample, not a human vote or an independent AI judge. Both versions passed these cases. This comparison was against the previously published consolidated advisor, not the retired version-one skill set or unskilled Codex. The older broad benchmark and full source audit were not resumed.

The saved result includes native turn IDs, confirmed runtime settings, commands, output hashes, and actual answers. Raw native logs stayed local; they can contain environment details and must be reviewed before publication. The committed fixture and runner support future repetition; one run is not proof that every possible answer will be correct.
