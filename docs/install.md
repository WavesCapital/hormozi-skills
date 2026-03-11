
# Install

## Claude Code

1. Copy the desired skill folders from `skills/` into your local skills directory.
2. Or symlink them into your project `.claude/skills/` directory.
3. Restart or refresh your skill environment if needed.

## Claude.ai

1. Zip an individual skill folder.
2. Upload it through Settings > Capabilities > Skills.

## Notes

- `hormoziskills` is the entry point router.
- Child skills are slash-invocable with names like `/hormozi-offers`.
- Some workflows assume you will locally supply licensed source materials if you want source-backed reasoning.
