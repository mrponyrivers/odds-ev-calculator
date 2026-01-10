import argparse
from datetime import datetime

from odds_ev_tool.core import (
    american_to_decimal,
    compute_row,
    kelly_fraction,
    parse_american_odds,
    read_bets_csv,
    write_csv,
)


def write_report(path: str, *, args, rows_out: list, plus_rows: list, errors: int,
                 avg_ev: float, avg_edge: float, total_stake: float) -> None:
    valid_rows = [r for r in rows_out if isinstance(r.get("edge"), float) and isinstance(r.get("ev_per_1"), float)]
    top_by_edge = sorted(valid_rows, key=lambda r: r["edge"], reverse=True)[:5]

    with open(path, "w", encoding="utf-8") as f:
        f.write("# Odds EV Tool Report\n")
        f.write(f"- Generated: {datetime.now().isoformat(timespec='seconds')}\n\n")

        f.write("## Run settings\n")
        f.write(f"- input: {args.input}\n")
        f.write(f"- output: {args.output}\n")
        f.write(f"- plus_output: {args.plus_output}\n")
        f.write(f"- report: {args.report}\n")
        f.write(f"- bankroll: {args.bankroll}\n")
        f.write(f"- kelly_scale: {args.kelly_scale}\n")
        f.write(f"- max_stake_pct: {args.max_stake_pct}\n")
        f.write(f"- min_ev: {args.min_ev}\n")
        f.write(f"- min_edge: {args.min_edge}\n\n")

        f.write("## Summary\n")
        f.write(f"- Rows kept: {len(rows_out)}\n")
        f.write(f"- Errors: {errors}\n")
        f.write(f"- +EV rows (ev >= {args.min_ev}): {len(plus_rows)}\n")
        f.write(f"- Avg EV per $1: {avg_ev:.4f}\n")
        f.write(f"- Avg edge: {avg_edge:.4f}\n")
        f.write(f"- Total recommended stake (sum): {total_stake:.2f}\n\n")

        f.write("## Top bets by edge (up to 5)\n")
        if not top_by_edge:
            f.write("- (none)\n")
        else:
            for r in top_by_edge:
                f.write(
                    f"- {r['bet_name']}: edge={r['edge']:.4f}, ev={r['ev_per_1']:.4f}, "
                    f"stake={float(r.get('rec_stake', 0.0)):.2f}\n"
                )


def main() -> None:
    parser = argparse.ArgumentParser(description="Odds EV Tool (CSV in -> CSV out)")
    parser.add_argument("--input", default="bets.csv", help="Input CSV (default: bets.csv)")
    parser.add_argument("--output", default="results.csv", help="Output CSV (default: results.csv)")
    parser.add_argument("--plus-output", default="plus_ev.csv", help="+EV output CSV (default: plus_ev.csv)")
    parser.add_argument("--report", default="report.md", help="Write a summary report (default: report.md)")

    parser.add_argument("--bankroll", type=float, default=500.0, help="Bankroll (default: 500)")
    parser.add_argument("--kelly-scale", type=float, default=0.25, help="Kelly scale (default: 0.25)")
    parser.add_argument("--max-stake-pct", type=float, default=0.05, help="Max stake %% of bankroll (default: 0.05)")

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

    avg_ev = (sum(ev_values) / len(ev_values)) if ev_values else 0.0
    avg_edge = (sum(edge_values) / len(edge_values)) if edge_values else 0.0
    total_stake = sum(rec_stakes) if rec_stakes else 0.0

    write_report(
        args.report,
        args=args,
        rows_out=rows_out,
        plus_rows=plus_rows,
        errors=errors,
        avg_ev=avg_ev,
        avg_edge=avg_edge,
        total_stake=total_stake,
    )
    print("Done.")
    print(f"- Rows kept: {len(rows_out)} (errors: {errors})")
    print(f"- +EV rows (ev >= {args.min_ev}): {len(plus_rows)}")
    if args.min_edge is not None:
        print(f"- Edge filter applied: edge >= {args.min_edge}")
    print(f"- Avg EV per $1: {avg_ev:.4f}")
    print(f"- Avg edge: {avg_edge:.4f}")
    print(f"- Total recommended stake (sum): {total_stake:.2f}")
    print(f"Wrote: {args.output}, {args.plus_output}, {args.report}")


if __name__ == "__main__":
    main()
