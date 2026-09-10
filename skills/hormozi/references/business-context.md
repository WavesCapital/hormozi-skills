# Business Context Contract

Writing rule: `HZ-SYN-004`. Use short words in all user-facing profile help. Define any exact profile term in plain words.

`BUSINESS.md` is the human source of truth for durable business context. `.hormozi/business.json` is generated state; never ask a human to maintain both.

## Complete Profile Sections

Use these headings or clear equivalents:

1. Status
2. Business Thesis
3. Customers and Expensive Problems
4. Offers and Mechanism
5. Economics
6. Acquisition
7. Sales
8. Delivery, Activation, and Retention
9. Proof
10. Current Constraint and Priorities
11. Claims, Safety, and Boundaries
12. Authorities and Freshness
13. Known Unknowns

To pass full-profile validation, the status must explicitly say `approved`. Unknown numbers should remain `unknown`; never invent them to satisfy validation. This is a saved-profile quality check, not a gate to every consultation. A draft can supply context without becoming approved evidence.

## What Belongs In The Profile

Keep stable summaries that materially change advice: business model, customer, painful problem, offer, mechanism, durable economics, acquisition and sales shape, delivery and activation, proof categories, strategic priorities, claims boundaries, and known unknowns.

Link rather than duplicate frequently changing operating metrics, product behavior owned by an executable repository, provider terms or signed economics, detailed sales or CRM procedures, proof libraries, live CRM or campaign state, and historical plans retained for context.

## Authority Links

Use ordinary Markdown links. Relative local paths are resolved from `BUSINESS.md`. Each link should be described in the surrounding text or an authority table with what the source owns, whether it is current or live-read-required, when it must be refreshed, and what must never be copied into the profile.

The resolver records path, existence, SHA-256, modification time, and read status. It does not copy linked file contents into the sidecar.

## Resolution Rules

Edit the profile only when the user explicitly asks. A request for advice or a skill audit does not grant that permission. Preserve unrelated content and verify any requested edit. Use `inspect` for routine read-only context, including incomplete profiles. Use `resolve --no-write` to check a complete approved profile without a sidecar write. Test edits with fictional profiles when real files are protected.

1. An explicit `--profile` wins.
2. Otherwise search from the working directory upward for the nearest `BUSINESS.md`.
3. Do not search sibling or child businesses implicitly.
4. Inspect without writing. Generate a sidecar beside the selected profile only during an authorized setup or refresh.
5. Recheck relevant facts before a material decision so a changed authority changes the next answer. Do not confuse the file's existence, hash or approval with verification of a claim.
6. If an authority needed for the question is missing, unreachable, stale, or conflicting, label the issue and stop only the affected conclusion.

## Sensitive Data Boundary

Do not place credentials, access tokens, customer applications, private identifiers, raw financial-account data, medical data, or live record dumps in `BUSINESS.md`, its sidecar, prompts, URLs, logs, or ordinary reports.
