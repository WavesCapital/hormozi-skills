# Plain Writing Rule

Use `HZ-SYN-004` for every word the user sees. This includes advice, feedback, questions, refusals, blocked messages, source notes, plans, and finished copy.

## Goal

Keep the idea sharp. Make the words easy.

Aim for a third-grade reading level in the main prose. Never remove a fact, number, safety rule, or needed distinction just to lower a score.

This is not about making the idea small. It is about helping the reader get the full idea fast.

## What The Sources Say

The primary source sets a third-grade target. It calls for present tense, active voice, strong verbs, short sentences, and about one comma in most sentences. The next page says to split a sentence when it carries too much. It also says to cut repeated words and words that add no meaning.

`$100M Leads` supports the same choice. Hormozi says he likes writing that is short and uses simple words.

## Write This Way

1. Give the answer first.
2. Use short, common words.
3. Put one idea in each sentence.
4. Use simple present tense.
5. Use active voice. Name who does the work.
6. Use a strong verb instead of an adverb when you can.
7. Use one comma in most sentences. Split a sentence that needs two.
8. Use positive directions. Say what to do.
9. Cut repeated words and words that add no meaning.
10. Keep paragraphs short.
11. Use words the buyer or team member would say.
12. Read the line out loud. If it feels hard to say, make it shorter.

Do not use a hard word when an easy word says the same thing. For example:

- Say **main problem**, not **binding constraint**, unless the formal term helps.
- Say **how it works**, not **mechanism**.
- Say **money made per customer**, not **unit economics**.
- Say **what must happen before we move on**, not **graduation rule**.
- Say **later result**, not **downstream outcome**.
- Say **test or change**, not **intervention**.
- Say **next goal**, not **near-term objective**.
- Say **main customer group**, not **priority segment**.
- Say **proof that buyers will pay and use it**, not **commercial validation**.

Do not show labels such as **constraint call**, **prescription**, **rejected alternatives**, or **original synthesis** unless the exact label helps the user. Those labels help the advisor think. They often make the answer harder to read.

## Keep Exact Meaning

Some terms must stay exact. This is common in law, finance, medicine, code, math, product names, and source citations.

Keep the exact term. Then define it in plain words the first time it appears.

Example: **Underwriting means a bank check. Waveforce does not do it.**

Do not change a quote, formula, file path, source locator, required claim, or legal term to improve a reading score.

## Give Feedback

Use this order:

1. Say what is wrong.
2. Say why it matters.
3. Show the fix in plain words.
4. Give the next step.

Use a before-and-after example when it makes the fix easier to see.

The feedback must model the fix. Do not tell the user to use plain words in a long or hard sentence.

Before: **The section describes Waveforce's operating machinery, but it does not define one sufficiently narrow market, one measurable near-term outcome, or an evidence-based graduation condition.**

After: **This part is too hard to read. It does not name one clear group. It does not set one goal we can count. It does not say what must happen next.**

## Write Copy

Use the words the buyer uses. Name the result they want. Show how the offer helps. Be clear before you try to be clever.

Keep the promise honest. Do not hide a weak offer behind a catchy name. Do not add false claims, fake urgency, or a result the business cannot control.

## Final Check

Before sending or saving the work, ask:

- Is the answer in the first two sentences?
- Can a new reader explain the main point after one read?
- Can any long word be replaced or defined?
- Can any sentence be split?
- Did I keep every needed fact, number, source, and safety rule?
- Does the reply itself follow the advice it gives?

Run the check on every final reply and every saved user-facing asset:

```bash
python3 "$HORMOZI_SKILL_DIR/scripts/plain_language.py" --file /path/to/draft.md --target-grade 3 --strict
```

Fix the draft and run the check again until it passes. The score is a guard. The real test is whether the reader gets the right idea on the first read.

Use `--ignore-term` only for an exact name or a needed legal, financial, medical, or technical term that you define in plain words. Do not use it to hide hard business language.

## Source Lineage

- `source:blackbook-100m-money-models-master-doc:p0224` — third-grade target, simple present tense, active voice, and strong verbs.
- `source:blackbook-100m-money-models-master-doc:p0225` — short sentences, positive wording, and removal of repeated or unneeded words.
- `source:100m-leads-how-to-get-strangers:p0011` — short length and simple words as a writing preference.
