# Missing-Profile Onboarding

Use `HZ-SYN-004` and [communication-standard.md](communication-standard.md) in every onboarding message.

Onboarding is a short talk, not a long form. Check the user's business files before you ask a question they already answer.

## Gate

Wait to give business advice until the user approves a valid `BUSINESS.md`. You may still audit the skill or explain a general Hormozi rule.

For a business request, onboarding is the whole answer until approval. Do not add tactics, citations, a growth plan, or a general rule. Explain the pause in one sentence. Ask only the next small set of questions. Say that you will draft the profile and wait for approval before giving advice.

## Interview Sequence

Ask only questions that can change the answer. Use small sets.

Do not combine the sets in one turn. Check the business files first. Skip questions the files answer. Mark an unsure answer as unknown. Do not guess.

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

After approval, copy `assets/business-profile-template.md` from this installed skill, fill it with the approved stable summary and links, then run from the absolute skill directory resolved by the entrypoint:

```bash
python3 "$HORMOZI_SKILL_DIR/scripts/business_context.py" validate --profile /absolute/path/BUSINESS.md
python3 "$HORMOZI_SKILL_DIR/scripts/business_context.py" resolve --profile /absolute/path/BUSINESS.md
```

Only begin personalized consulting after both commands pass.
