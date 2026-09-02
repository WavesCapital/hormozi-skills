# Diagnose & Sequence

Writing rule: `HZ-SYN-004`. Say **main problem** in the answer. Use **binding constraint** only when the exact term helps, then define it.

Find the binding constraint, choose the correct stage and sequence, and define the smallest measurable intervention.

## Workflow

1. Resolve current business facts and the desired outcome.
2. Map volume, rates, delay, capacity, and economics across the value flow.
3. Call one binding constraint and reject non-binding work.
4. Choose one experiment and graduation rule.

## Material Rules

### HZ-DIA-001 — One binding constraint

Treat growth as a constrained system: direct the next intervention at the limiting step, not at capacity elsewhere.

Decision logic:

- Map the current value flow from demand through delivery and cash.
- Locate the step whose relief would increase total throughput.
- Reject work that only increases potential before or after that step.

Citations:

- `source:blackbook-100m-money-models-master-doc:p0170` (primary)

### HZ-DIA-002 — Measure multiplicative throughput

Model the commercial path as multiplicative conversion stages so a weak rate cannot hide inside an aggregate total.

Decision logic:

- Define each stage and denominator before comparing periods.
- Calculate the absolute output and rate at each handoff.
- Prioritize the rate or capacity change with the largest credible downstream gain.

Citations:

- `source:100m-lead-nurture-playbook:p0009` (primary)
- `source:100m-leads-how-to-get-strangers:p0238` (supporting)

### HZ-DIA-003 — Do not maximize local utilization

A fully booked resource can reduce total conversion when it pushes appointments out, removes convenient slots, or eliminates follow-up capacity.

Decision logic:

- Measure total downstream conversion, not calendar fullness.
- Preserve capacity for fast booking, outbound follow-up, and six-inch putts.
- Add capacity or reshape calendars when utilization creates a queue.

Limits:

- A short, controlled utilization spike is acceptable when downstream service and follow-up remain protected.

Citations:

- `youtube:A_tx40lNpf8:t001544799-t001606960` (dated_refinement) — https://www.youtube.com/watch?v=A_tx40lNpf8&t=1544s

### HZ-DIA-004 — Stage before tactic

Sequence advice by the verified operating stage rather than jumping to a later-stage system because it is sophisticated or fashionable.

Decision logic:

- Classify the business against the roadmap evidence.
- Complete the current stage's graduation condition.
- Load later-stage doctrine only when the current stage no longer binds.

Citations:

- `source:your-acq-100mscalingroadmap-stage0:p0002` (roadmap_stage)
- `source:your-acq-100mscalingroadmap-stage01:p0002` (roadmap_stage)
- `source:your-acq-100mscalingroadmap-stage02:p0002` (roadmap_stage)
- `source:your-acq-100mscalingroadmap-stage03:p0002` (roadmap_stage)
- `source:your-acq-100mscalingroadmap-stage04:p0002` (roadmap_stage)
- `source:your-acq-100mscalingroadmap-stage05:p0002` (roadmap_stage)
- `source:your-acq-100mscalingroadmap-stage06:p0002` (roadmap_stage)
- `source:your-acq-100mscalingroadmap-stage07:p0002` (roadmap_stage)
- `source:your-acq-100mscalingroadmap-stage08:p0002` (roadmap_stage)
- `source:your-acq-100mscalingroadmap-stage09:p0002` (roadmap_stage)

### HZ-DIA-005 — More, better, then new

Exploit a working acquisition path through volume and improvement before adding a new placement, platform, or lead method.

Decision logic:

- Ask what prevents ten times the current activity.
- Do more if capacity and unit economics permit.
- Improve the newly exposed drop-off.
- Add a new placement, then platform, then Core Four method only after more/better is exhausted.

Limits:

- For businesses above roughly $1M annual profit, percentage improvements may outrank raw volume; verify economics rather than applying the threshold mechanically.

Citations:

- `source:100m-leads-how-to-get-strangers:p0243` (primary)
- `source:100m-leads-how-to-get-strangers:p0244` (primary)

### HZ-DIA-006 — One measurable intervention

Translate diagnosis into the smallest test that can relieve the constraint and define the next decision before execution.

Decision logic:

- State the rejected alternatives and why they are not binding.
- Choose one owner, one observable leading indicator, and one decision date.
- Graduate, iterate, or stop from the measured result.

Citations:

- `source:blackbook-100m-money-models-master-doc:p0170` (primary)
- `source:100m-leads-how-to-get-strangers:p0244` (supporting)

## Output Check

Use the plain answer shape in `../answer-contract.md`. Tell the user the main problem, why it matters, what to do, what not to do yet, and the next step. Show the math and sources when they help. Keep unknown facts and safety limits clear. Do not use internal labels as headings. Run the strict writing check, fix the draft, and check it again.
