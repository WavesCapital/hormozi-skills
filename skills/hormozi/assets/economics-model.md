# Money Check

Doctrine lineage: `HZ-OFE-005`, `HZ-OFE-008`, `HZ-OFE-009`, `HZ-OFE-010`.
Writing rule: `HZ-SYN-004`. Use short words and short sentences. Explain any hard term.

Run `python3 "$HORMOZI_SKILL_DIR/scripts/economics.py" --help` when you need the same math every time.

The `unit` helper estimates gross profit, not cash flow. Use earned monthly sales for one buyer. Its upfront fields are for a separate one-time sale and its cost. Do not put prepaid monthly service there too. That would count the same sale twice. See `unit --help` for each input. JSON schema 2 names the revenue fields as earned, not collected.

## Starting Numbers

| Number | Best guess | Low | High | Fact state |
|---|---:|---:|---:|---|
| Price for each service period or purchase | | | | |
| Leads in the same group | | | | |
| Buy rate | | | | |
| Cost to serve one buyer per period or purchase | | | | |
| Cost to get one buyer | | | | |
| Paid periods or buys per buyer | | | | |
| Buyers lost each month | | | | |

Use the same time span and buyer group for each price. Keep facts apart from guesses.

Check what each cost covers before naming the result. Missing delivery labor means gross profit is not yet known. Show money left after the listed costs instead. Net profit needs all costs. Keep cost gaps beside each result and in the final claim. Unknown costs are not zero. When the figures are complete, use them.

## Math

```text
gross profit per purchase = earned sales revenue - delivery cost for that purchase
lifetime gross profit = gross profit per purchase × purchases per customer
gross profit per lead = buy rate × lifetime gross profit
acquisition contribution = lifetime gross profit - acquisition cost
funnel output = input volume × conversion rate at each stage
```

Use this simple math only when price and cost stay fixed across those purchases. Otherwise sum the actual sales and costs. Include added overhead to see the firm's profit. Do not count the same payment twice.

## Cash and Work Owed

- Cash collected now:
- Work that cash must still pay for:
- Refunds or claims the firm may owe:
- Dates of later bills and costs:
- Full price and term the buyer agrees to:

Prepaid cash is not all profit today. A later fee and a waiver are different paths. Compare them using the share of buyers who take each path.

## Pick the Next Move

- Main number holding back profit:
- Number that changes the result most:
- Break-even:
- Range to test:
- Safety limit:
