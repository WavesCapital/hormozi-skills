---
name: hormozi-pricing
description: "This skill should be used when the user asks what to charge, how to restructure packages, how to improve profit, or how to raise prices safely."
---

# Hormozi Pricing

Set prices, restructure packages, and plan safe price raises.

## Use Cases

- What should we charge for this?
- How do we raise prices safely?
- Compare monthly vs annual pricing

## Primary Outputs

- pricing-model recommendation
- package ladder
- instant-profit play shortlist
- raise plan and letter

## Hard Boundaries

- Not full money-model architecture
- Not offer strategy outside price/packaging
- Not churn diagnosis except pricing-linked churn risk

## Composition

- Composes with: `hormozi-offers`, `hormozi-customer-value`, `hormozi-money-models`
- Preferred sequence: Use after the offer exists but before broad monetization redesign.

## Source Loading Rules

1. Start with `references/framework.md`.
2. Then open `references/source-map.md` for exact source ownership and sibling handoffs.
3. If local raw source markdown exists under `references/raw/`, use it selectively.
4. Do not dump long source excerpts into the response.

## Required Assets

- price-architecture-sheet
- raise-letter-template
- pricing-impact-model

## Trigger Examples

- What should we charge for this?
- How do we raise prices safely?
- Compare monthly vs annual pricing

## Non-Trigger Examples

- Get us more leads
- Map our whole monetization ladder
