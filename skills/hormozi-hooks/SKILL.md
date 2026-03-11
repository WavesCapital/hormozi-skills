---
name: hormozi-hooks
description: "This skill should be used when the user asks for hooks for ads, content, email, or social, wants to improve weak openings, or wants to adapt hooks across channels."
---

# Hormozi Hooks

Generate, score, and adapt hooks across channels using Hormozi hook frameworks.

## Use Cases

- Give me 30 hooks for this offer
- Improve these opening lines
- Adapt these hooks for email and YouTube

## Primary Outputs

- hook bank by angle
- platform adaptation matrix
- test shortlist
- verbal/nonverbal hook variants

## Hard Boundaries

- Not full ad assembly
- Not offer diagnosis
- Not brand strategy

## Composition

- Composes with: `hormozi-goated-ads`, `hormozi-leads`, `hormozi-launch-campaigns`
- Preferred sequence: Use before goated-ads when only the opening needs work.

## Source Loading Rules

1. Start with `references/framework.md`.
2. Then open `references/source-map.md` for exact source ownership and sibling handoffs.
3. If local raw source markdown exists under `references/raw/`, use it selectively.
4. Do not dump long source excerpts into the response.

## Required Assets

- hook-angle-matrix
- platform-hook-sheet
- hook-test-grid

## Trigger Examples

- Give me 30 hooks for this offer
- Improve these opening lines
- Adapt these hooks for email and YouTube

## Non-Trigger Examples

- Write the whole ad campaign
- Diagnose our pricing model
