# Missing-Profile Onboarding

Use `HZ-SYN-004` and [communication-standard.md](communication-standard.md) in every onboarding message.

Onboarding is a short talk, not a long form. Check the user's business files before you ask a question they already answer.

This is setup for the advisor, not proof that the business is starting from zero. A firm can be mature and have no profile. First learn what it does and what the owner wants help with. Do not reset its market, choose its first offer, or stop its existing work just because this file is missing.

## Help First, Fill The Gaps

If there is no profile, begin helping the user build one. Use the facts already in the conversation and authorized business files. Explain briefly that a saved profile helps future advice. Do not make approval of a complete profile the price of answering a narrow question.

If the request is simply to get started and contains no business facts, the first reply is a short welcome, the purpose of the linked profile, and a few questions about the business and current goal. Save the strategy for when those answers support it. No source search is needed just to ask these questions. Do not turn the whole question bank below into one message.

Give advice the known facts support. When a missing fact changes the choice, ask for it or explain what you would do in each case. If facts are too thin for a sound choice, say what you need and why. Do not guess a business's costs, proof, capacity or results. Keep draft facts and approved records distinct.

For example, a price and a per-sale cost can settle which of two discounts keeps more money. You do not need the whole sales history to do that math. But a claim that a new price will raise total profit needs facts about demand too. Ask only for what can change this decision.

## Interview Sequence

Ask only questions that can change the answer. Use small sets.

These sets are a question bank, not four required turns. Start with the user's current question. Check the business files first. Skip questions already answered. Ask one or a few useful questions at a time; mark an unsure answer as unknown.

### Batch 1: Business And Customer

- What do you sell? Who buys it? How does it help them?
- What costly or urgent problem does the buyer already know they have?
- What result does the buyer want? What do they use now?

### Batch 2: Offer And Economics

- What is the offer? What does it cost? When does the buyer pay?
- What does it cost you to serve one buyer? How much gross profit remains?
- What must happen before the buyer gets the first useful result? What is the full result?
- Which numbers are proven, guessed, or unknown?

### Batch 3: Commercial Path

- How does a new person hear about you, talk with you, buy, get a result, and buy again?
- How many people reach each step? How many move on? How long does each step take?
- Where does the team run out of time or room to do more work?

### Batch 4: Proof, Constraint, And Boundaries

- What proof supports the promise? What must you not claim?
- What result matters most now? Where do you think people get stuck?
- Which files or live tools hold facts that change often?

## Synthesize Before Writing

Explain what the business does, how buyers get value, how the business makes money, and where people may get stuck. Separate facts from guesses. List the source links you plan to use. Ask the user to fix and approve the draft. Do not mark it approved for them.

## Create The Profile

When the user asks to create or save the profile, use `assets/business-profile-template.md` as a starting point. Keep unknowns clear and link changing facts to their owners. Save a draft as a draft; set approved status only after the user approves it. Do not overwrite an existing profile or change its approved sections without a request. For an approved profile, run from the absolute skill directory resolved by the entrypoint:

```bash
python3 "$HORMOZI_SKILL_DIR/scripts/business_context.py" validate --profile /absolute/path/BUSINESS.md
python3 "$HORMOZI_SKILL_DIR/scripts/business_context.py" resolve --profile /absolute/path/BUSINESS.md
```

These checks verify the saved profile, not the truth of every business fact. A failed format check calls for a profile fix within the user's request; it does not block advice supported by the facts already known. In a read-only task, do not run the writing command or create the profile. Use fictional fixtures for edit tests.
