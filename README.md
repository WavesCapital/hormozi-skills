# Hormozi Skills

Public-safe skill library for Claude Code, Claude.ai, and compatible skill runtimes.

This repo packages a **Hormozi-style business operator system** as a set of reusable skills:

- one router skill: `hormoziskills`
- fourteen focused child skills like `hormozi-offers`, `hormozi-leads`, and `hormozi-pricing`
- a public catalog, routing rules, and install docs

The goal is simple:

Instead of remembering which framework lives in which book or playbook, invoke one router and let it point you to the right skill.

## What This Repo Does

This repo gives you a **public framework** for a Hormozi-inspired skill system.

It is designed to help with questions like:

- Which skill should I use for this problem?
- How do I improve this offer?
- How do I get more qualified leads?
- How should I price this?
- How do I increase LTV and retention?
- What stage is this business in?
- How should I structure a launch campaign?

## The Entry Point

Start with:

- `/hormoziskills`

This is the router skill. Its job is to:

- understand the business problem
- choose the best `hormozi-*` skill
- recommend one primary skill and up to two supporting skills
- avoid sending you into the wrong framework

If you already know what you want, call a child skill directly.

Examples:

- `/hormozi-offers`
- `/hormozi-leads`
- `/hormozi-money-models`
- `/hormozi-pricing`

## Included Skills

### Router

- `hormoziskills`: choose the right Hormozi skill or combination of skills

### Core Strategy

- `hormozi-offers`: improve offers, value equation, guarantees, bonuses, naming
- `hormozi-leads`: choose and improve lead-generation systems
- `hormozi-money-models`: redesign monetization structure and ascension logic
- `hormozi-pricing`: set prices, restructure packages, raise prices safely
- `hormozi-customer-value`: increase LTV, retention, and fast cash from the base
- `hormozi-scaling-roadmap`: diagnose business stage, bottlenecks, priorities
- `hormozi-team-scaling`: improve team cadence, communication, and service systems

### Attention And Conversion

- `hormozi-hooks`: generate and adapt hooks across channels
- `hormozi-goated-ads`: turn offers into direct-response ad systems
- `hormozi-lead-nurture`: improve follow-up, scheduling, and show rates
- `hormozi-closing`: improve objection handling and close rate
- `hormozi-proof`: identify and deploy stronger proof
- `hormozi-branding`: build fame, authority, and memorability
- `hormozi-launch-campaigns`: plan launches, VSL funnels, affiliate flows, and event-style campaigns

## Quickstart

### Claude Code

Copy or symlink the desired skill folders from `skills/` into your local skills directory.

Typical project setup:

```bash
mkdir -p .claude/skills
ln -s /path/to/hormozi-skills/skills/hormoziskills .claude/skills/hormoziskills
ln -s /path/to/hormozi-skills/skills/hormozi-offers .claude/skills/hormozi-offers
ln -s /path/to/hormozi-skills/skills/hormozi-leads .claude/skills/hormozi-leads
```

If you want the whole set, link all of the `skills/hormozi-*` folders.

### Claude.ai

Zip an individual skill folder and upload it in:

`Settings > Capabilities > Skills`

Start with the router:

- zip `skills/hormoziskills/`
- upload it first

Then upload whichever child skills you want available directly.

## Example Prompts

### Router-first

```text
Check /hormoziskills and use the relevant skills for this SaaS pricing and upsell problem.
```

```text
Which Hormozi skill should I use to improve this offer and make it easier to sell?
```

```text
Route this to the right Hormozi skill: our booked leads are ghosting and our show rate is awful.
```

### Child-skill direct

```text
/hormozi-offers Rebuild this consulting package so it feels irresistible.
```

```text
/hormozi-leads Diagnose why our lead flow stalled and what channels we should test next.
```

```text
/hormozi-pricing Compare monthly, annual, and hybrid pricing for this offer.
```

## Public Core, Private Overlay

This repo intentionally ships a **public-safe core**.

Included here:

- skill instructions
- router logic
- catalog and routing docs
- public metadata
- install docs
- public-safe source policy

Not included here:

- proprietary or copyrighted source PDFs
- raw extracted markdown from those sources
- private source ownership internals
- launch assets, media, blackbooks, spreadsheets, or exact source packs

If you want source-backed behavior, use your own licensed source materials locally.

Read:

- [Install docs](docs/install.md)
- [Architecture](docs/architecture.md)
- [Source policy](docs/source-policy.md)

## Repo Layout

```text
skills/
  hormoziskills/
  hormozi-offers/
  hormozi-leads/
  ...
docs/
  install.md
  architecture.md
  source-policy.md
```

Each child skill is intentionally narrow.
The router helps choose between them.

## Design Principles

This repo follows a few strong rules:

- one skill = one narrow business outcome
- router chooses, child skills execute
- no giant mega-skill
- public releases stay source-safe
- skills should be slash-invocable and composable
- catalogs and routing rules should be easy to maintain

## Who This Is For

This repo is for:

- operators who want a reusable Hormozi-style framework
- founders who want structured help with offers, leads, pricing, and monetization
- AI-agent builders who want a clean skill architecture around business frameworks
- teams who want a public-safe skill system without shipping copyrighted source packs

## Current Status

This is an active framework repo.

The public version is intentionally conservative:

- it is usable as a routing and skill architecture system today
- it does not bundle proprietary source material
- some source-heavy behavior may require local private overlays

## Roadmap

Likely next improvements:

- better install automation
- release packaging for individual zipped skill bundles
- richer public examples and screenshots
- import/hydration scripts for user-supplied local source packs
- stronger regression cases for router collisions and planned-skill fallback

## License

See [LICENSE](LICENSE).

The license covers the original framework and docs in this repo.
It does **not** grant rights to third-party or user-supplied source materials.
