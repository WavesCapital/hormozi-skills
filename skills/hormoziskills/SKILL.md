---
name: hormoziskills
description: "This skill should be used when the user asks \"check /hormoziskills\", \"which Hormozi skill should I use\", \"route this to the right Hormozi skill\", \"show me the Hormozi skill catalog\", or \"pick the best hormozi-* skill for this\". Do not use this skill for general marketing work when a specific hormozi-* skill is already clearly indicated."
user-invocable: true
disable-model-invocation: false
---

# Hormozi Skills Router

Route requests to the right Hormozi skill or combination of skills.

## Use This Skill For

Use this skill when the user explicitly asks which Hormozi skill to use, wants to inspect the Hormozi skill catalog, or asks to route a task to the best `hormozi-*` skill.

## Do Not Use This Skill For

- Direct domain work when the user already named a specific `hormozi-*` skill
- Generic marketing tasks that should be handled by a child skill directly
- Non-Hormozi skill routing

## Routing Algorithm

1. If the user already named a specific `hormozi-*` skill, do not interpose.
2. Read `references/catalog.md` only when routing is actually needed.
3. Rank candidate skills by outcome match.
4. Return one primary skill and at most two supporting skills.
5. If the best skill is planned or unavailable, say so clearly and use the declared fallback.
6. Do not perform the child skill's work inside this skill.

## Catalog Files

- `references/catalog.yaml`: structured source of truth
- `references/catalog.public.yaml`: sanitized public catalog
- `references/catalog.md`: human-readable table of contents
- `references/selection-rules.md`: routing and composition rules
- `references/router-cases.md`: trigger and non-trigger regression cases
- `references/source-ownership.private.md`: private corpus coverage and source ownership
- `references/public-release-model.md`: public GitHub release rules
- `references/source-policy.md`: public-safe source policy
- `references/corpus-inventory.md`: file-level classification of the full source corpus

## Output Format

Return:

- `Primary skill:` `hormozi-*`
- `Supporting skills:` zero to two `hormozi-*` skills
- `Why:` one short explanation
- `Status:` available / planned for each recommended skill
