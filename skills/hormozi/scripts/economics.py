#!/usr/bin/env python3
"""Simple funnel and gross-profit estimates with explicit assumptions."""

from __future__ import annotations

import argparse
import json
import math


def parse_stage(value: str) -> tuple[str, float]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("stage must be NAME=COUNT")
    name, raw_count = value.split("=", 1)
    try:
        count = float(raw_count)
    except ValueError as error:
        raise argparse.ArgumentTypeError("stage count must be numeric") from error
    if not name.strip() or count < 0 or not math.isfinite(count):
        raise argparse.ArgumentTypeError("stage needs a name and a finite non-negative count")
    return name.strip(), count


def funnel(stages: list[tuple[str, float]]) -> dict[str, object]:
    if len(stages) < 2:
        raise ValueError("at least two stages are required")
    rows = []
    for index, (name, count) in enumerate(stages):
        prior = stages[index - 1][1] if index else None
        if prior is not None and count > prior:
            raise ValueError(f"stage {name} exceeds the previous stage")
        rows.append({
            "name": name,
            "count": count,
            "conversion_from_prior": None if prior is None or prior == 0 else count / prior,
            "loss_from_prior": None if prior is None else prior - count,
            "conversion_from_start": None if stages[0][1] == 0 else count / stages[0][1],
        })
    bottleneck = min(rows[1:], key=lambda row: row["conversion_from_prior"] if row["conversion_from_prior"] is not None else 1.0)
    return {
        "calculation": "funnel",
        "stages": rows,
        "lowest_stage_conversion": bottleneck["name"],
        "warning": "The lowest conversion is a diagnostic candidate, not proof of the binding constraint; check economics and capacity.",
    }


def unit(args: argparse.Namespace) -> dict[str, object]:
    values = [args.monthly_revenue, args.gross_margin, args.cac, args.monthly_churn, args.upfront_revenue, args.upfront_variable_cost]
    if any(value < 0 or not math.isfinite(value) for value in values):
        raise ValueError("all inputs must be finite and non-negative")
    if args.gross_margin > 1 or args.monthly_churn > 1:
        raise ValueError("gross margin and monthly churn must be decimals from 0 to 1")
    monthly_gross_profit = args.monthly_revenue * args.gross_margin
    upfront_gross_profit = args.upfront_revenue - args.upfront_variable_cost
    lifetime_months = None if args.monthly_churn == 0 else 1 / args.monthly_churn
    lifetime_gross_profit = None if lifetime_months is None else upfront_gross_profit + monthly_gross_profit * lifetime_months
    payback = 0.0 if upfront_gross_profit >= args.cac else (
        None if monthly_gross_profit == 0 else (args.cac - upfront_gross_profit) / monthly_gross_profit
    )
    return {
        "calculation": "unit_economics",
        "schema_version": 2,
        "inputs": {
            "monthly_earned_revenue": args.monthly_revenue,
            "gross_margin": args.gross_margin,
            "customer_acquisition_cost": args.cac,
            "monthly_customer_churn": args.monthly_churn,
            "upfront_earned_revenue": args.upfront_revenue,
            "upfront_variable_cost": args.upfront_variable_cost,
        },
        "outputs": {
            "monthly_gross_profit": monthly_gross_profit,
            "upfront_gross_profit": upfront_gross_profit,
            "simple_expected_lifetime_months": lifetime_months,
            "simple_lifetime_gross_profit": lifetime_gross_profit,
            "simple_ltv_to_cac": None if lifetime_gross_profit is None or args.cac == 0 else lifetime_gross_profit / args.cac,
            "simple_payback_months": payback,
        },
        "assumptions": [
            "Revenue, margin, acquisition cost, and churn describe the same customer cohort.",
            "Monthly revenue is earned per active customer for one service month, not cash collected that month.",
            "Upfront revenue and cost cover a separate one-time purchase, never service already counted in monthly revenue or margin.",
            "An annual prepayment for the monthly service is not extra upfront revenue. Model its receipt and future costs separately.",
            "Gross margin includes the delivery costs for the same monthly work. The upfront cost covers the separate one-time work.",
            "The simple churn model assumes a constant monthly churn hazard and no expansion or discounting.",
            "A zero churn input means lifetime and lifetime value are unknown, not infinite.",
            "Simple payback is when modeled gross profit covers acquisition cost, not a forecast of bank cash or billing dates.",
            "Gross profit excludes overhead and tax. Use a dated cash-flow model for prepayments, refunds, delayed costs, or changing margins.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    funnel_parser = commands.add_parser("funnel")
    funnel_parser.add_argument("--stage", action="append", type=parse_stage, required=True)
    unit_parser = commands.add_parser(
        "unit", description="Estimate gross profit per customer, not cash flow. "
        "JSON schema 2 uses earned-revenue input labels instead of collected-revenue labels."
    )
    unit_parser.add_argument("--monthly-revenue", type=float, required=True,
                             help="Revenue earned per active customer for one service month; not prepaid cash")
    unit_parser.add_argument("--gross-margin", type=float, required=True,
                             help="Monthly gross profit / monthly earned revenue, from 0 to 1")
    unit_parser.add_argument("--cac", type=float, required=True,
                             help="Cost to get one customer in the same group")
    unit_parser.add_argument("--monthly-churn", type=float, required=True,
                             help="Share of active customers lost per month, from 0 to 1")
    unit_parser.add_argument("--upfront-revenue", type=float, default=0.0,
                             help="Earned revenue for a separate one-time purchase; exclude prepaid monthly service")
    unit_parser.add_argument("--upfront-variable-cost", type=float, default=0.0,
                             help="Delivery cost for that separate one-time purchase; do not count monthly costs twice")
    args = parser.parse_args()
    try:
        result = funnel(args.stage) if args.command == "funnel" else unit(args)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except ValueError as error:
        print(json.dumps({"error": str(error), "ok": False}, indent=2, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
