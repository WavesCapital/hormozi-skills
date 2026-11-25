---
name: call-notes
description: Turns a sales call transcript into clean, concise handoff notes in a fixed 6-field format ready to paste into any CRM. Use whenever someone pastes or uploads a sales call, discovery call, setter/SDR call, or appointment transcript and wants notes, a summary, a handoff for the closer, or CRM notes. Works for any business, B2B or B2C.
---

# Call Notes

> **To customize:** Fill in "Your Business" below, or upload this file to Claude and say: "Customize this for my business: I sell [X] to [Y]..." Leave it blank and the skill still works.

## Your Business (optional, fill in once)

Write your answer after each colon and delete the e.g. examples.

- **What you sell:** (e.g. "Roof replacements" / "12-week fitness coaching" / "Payroll software" / "Life insurance")
- **Who you sell to:** (e.g. "Homeowners 50+" / "Busy moms" / "Business owners doing $1M+" / "HR managers")
- **Your key numbers:** (e.g. "Revenue & profit" / "Weight & body fat" / "Monthly electric bill" / "Savings & retirement age")
- **Your problem categories:** 3–6 one-word buckets (e.g. "Sales, Marketing, Operations, People" / "Nutrition, Consistency, Time" / "Cost, Trust, Timing")
- **Your deal breakers:** must be true to buy (e.g. "Must own home" / "Minimum $5k budget" / "Must be in Texas" / "Can attend in March")

Always ignore anything inside "(e.g. ...)". Those are placeholder examples, not this business. Use only what the person wrote. If a line has nothing else, infer it from the transcript.

---

## Purpose

Turn a call transcript into notes that let the next person (closer, manager, or the same rep later) understand the prospect in 30 seconds without re-reading the call or making the prospect repeat themselves.

## Output Format

Follow this format exactly. Output nothing before or after it. Bold only the field headers.

```
**Who:**
**Current → Goal:**
**Problem:**
**Decision:**
**Objections:**
**Extra Notes:**

Missing:
```

## Field Rules

**Who:** 2–10 words. As short as possible; longer only when the detail matters. The business type or the person's situation. If they have multiple businesses, name the one they want help with.
- "Med spa, 2 locations" / "Retail manager, 29, career switcher" / "Commercial cleaning, 40 staff, two states"

**Current → Goal:** Under 25 words. Where they are now → where they want to be, with a timeline. Use numbers whenever possible, using the key numbers above if set.
- "$2.4M revenue, slow summers → $4M in 2 years, booked year-round"
- "240 lbs, pre-diabetic → 200 lbs in 6 months"

**Problem:** Under 25 words, in this order: Category tag: what's stopping them. "Their exact quote." Consequence (what it costs them).
- Use the problem categories above if set; otherwise pick the clearest one-word category.
- Name only the most important problem.
- Example: Sales: Owner runs every estimate. "If I stop selling, we stop eating." Turning down $40k in jobs monthly.

**Decision:** Under 10 words. Who decides and who else must be involved. Name partners or spouses if mentioned, and whether they must be on the next call.
- "Sole owner" / "50/50 partner Mike, must be on call" / "Joint, wife manages money"

**Objections:** Under 10 words. The main objection only (the real one, not just the first one said). Category: their words. Categories: Time, Money, Authority, Trust, Preference, Stall. Use Trust when they were burned before or doubt the offer.
- Money: "Last agency burned $30k"

**Extra Notes:** Up to 3 one-line bullets. Only what the next person needs to know. Put any deal breakers from Your Business here first. Write "—" if nothing qualifies.

**Missing:** List every field the transcript didn't cover. Also list the missing part of a split field: Current, Goal, or Consequence. Write "none" if complete.

## Rules

1. Never guess. If it wasn't said, write "—" and list it under Missing. Never invent numbers.
2. Always show all 6 fields, in this order, every time.
3. Use the prospect's exact words in quotes when they're stronger than a paraphrase.
4. Stay under every word limit.
5. Leave out follow-up scheduling; the calendar tracks that.
6. Identify which speaker is the prospect. Only the prospect's statements go in the notes; ignore the rep's pitch. Rep read-backs of the prospect's info (e.g. "I have you at $2M, right?") count unless the prospect corrects them.
7. If the input has multiple calls or older notes, combine them and let the newest information win.
8. No commentary, advice, or summaries outside the format.

## Examples

**B2B**

**Who:** Personal injury law firm, 3 attorneys
**Current → Goal:** 22% lead-to-client rate → 35% by Q3
**Problem:** Sales: Intake misses callbacks. "We pay $400 a lead and let them go to voicemail." Losing cases to competitors.
**Decision:** Managing partner, other partners must approve
**Objections:** Authority: "Need partner buy-in first"
**Extra Notes:** —

Missing: none

**B2C**

**Who:** Homeowner, single-family, Arizona
**Current → Goal:** — → Lower bills before rates rise next year
**Problem:** Cost: Bills climb every summer. "July was $520." Squeezing the family budget.
**Decision:** Both spouses, husband skeptical
**Objections:** Money: "Heard solar doesn't pay off"
**Extra Notes:**
- Roof is 15 years old

Missing: Current

**Incomplete call**

**Who:** Skincare brand, Shopify, DTC
**Current → Goal:** $6M revenue, unclear margins → know true profit by product before raising prices
**Problem:** Finance: Bookkeeper only reconciles monthly. "I don't know if we're making money." —
**Decision:** Co-founders, 50/50, both on call
**Objections:** —
**Extra Notes:** —

Missing: Consequence, Objections
