import argparse

from odds_ev_tool.core import (
    american_to_decimal,
    compute_row,
    kelly_fraction,
    parse_american_odds,
    read_bets_csv,
    write_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Odds EV Tool (CSV in -> CSV out)")
    parser.add_argument("--input", default="bets.csv", help="Input CSV (default: bets.csv)")
    parser.add_argument("--output", default="results.csv", help="Output CSV (default: results.csv)")
    parser.add_argument("--plus-output", default="plus_ev.csv", help="+EV output CSV (default: plus_ev.csv)")

    parser.add_argument("--bankroll", type=float, default=500.0, help="Bankroll (default: 500)")
    parser.add_argument("--kelly-scale", type=float, default=0.25, help="Kelly scale (default: 0.25)")
    parser.add_argument("--max-stake-pct", type=float, default=0.05, help="Max stake % of bankroll (default: 0.05)")

    # Filters (job-like feature)
    parser.add_argument("--min-ev", type=float, default=0.0, help="Min EV to include in plus_ev.csv (default: 0.0)")
    parser.add_argument("--min-edge", type=float, default=None, help="Optional: only include rows with edge >= this value")

    args = parser.parse_args()

    raw_rows = read_bets_csv(args.input)

    rows_out = []
    errors = 0

    ev_values = []
    edge_values = []
    rec_stakes = []

    for row in raw_rows:
        try:
            bet_name = (row.get("bet_name") or "").strip() or "Unnamed"
            american = parse_american_odds((row.get("american_odds") or "").strip())
            win_prob = float((row.get("win_prob") or "").strip())

            base = compute_row(bet_name, american, win_prob)

            # Optional filter by edge
            if args.min_edge is not None and base["edge"] < args.min_edge:
                continue

            dec = american_to_decimal(american)
            kf = kelly_fraction(win_prob, dec)

            rec_stake = args.bankroll * kf * args.kelly_scale
            rec_stake = min(rec_stake, args.bankroll * args.max_stake_pct)
            rec_stake = max(0.0, rec_stake)

            base["kelly_fraction"] = round(kf, 4)
            base["rec_stake"] = round(rec_stake, 2)
            base["decision"] = "+EV" if base["ev_per_1"] > 0 else ("-EV" if base["ev_per_1"] < 0 else "EV=0")

            rows_out.append(base)

            # Summary tracking
            ev_values.append(base["ev_per_1"])
            edge_values.append(base["edge"])
            rec_stakes.append(base["rec_stake"])

        except Exception as e:
            errors += 1
            rows_out.append({
                "bet_name": row.get("bet_name", ""),
                "american_odds": row.get("american_odds", ""),
                "win_prob": row.get("win_prob", ""),
                "decimal_odds": "",
                "implied_prob": "",
                "edge": "",
                "ev_per_1": "",
                "kelly_fraction": "",
                "rec_stake": "",
                "decision": f"ERROR: {e}",
            })

    fieldnames = [
        "bet_name", "american_odds", "win_prob",
        "decimal_odds", "implied_prob", "edge", "ev_per_1",
        "kelly_fraction", "rec_stake", "decision"
    ]

    write_csv(args.output, fieldnames, rows_out)

    plus_rows = [r for r in rows_out if isinstance(r.get("ev_per_1"), float) and r["ev_per_1"] >= args.min_ev]
    write_csv(args.plus_output, fieldnames, plus_rows)

    # Print summary (job-like)
    kept = len(rows_out)
    plus_count = len(plus_rows)
    avg_ev = (sum(ev_values) / len(ev_values)) if ev_values else 0.0
    avg_edge = (sum(edge_values) / len(edge_values)) if edge_values else 0.0
    total_stake = sum(rec_stakes) if rec_stakes else 0.0

    print("Done.")
    print(f"- Rows kept: {kept} (errors: {errors})")
    print(f"- +EV rows (ev >= {args.min_ev}): {plus_count}")
    if args.min_edge is not None:
        print(f"- Edge filter applied: edge >= {args.min_edge}")
    print(f"- Avg EV per $1: {avg_ev:.4f}")
    print(f"- Avg edge: {avg_edge:.4f}")
    print(f"- Total recommended stake (sum): {total_stake:.2f}")
    print(f"Wrote: {args.output} and {args.plus_output}")


if __name__ == "__main__":
    main()
