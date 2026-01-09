import csv
from typing import Optional


def american_to_decimal(american: int) -> float:
    if american == 0:
        raise ValueError("American odds cannot be 0.")
    if american > 0:
        return 1.0 + (american / 100.0)
    return 1.0 + (100.0 / abs(american))


def decimal_to_implied_prob(decimal_odds: float) -> float:
    if decimal_odds <= 1.0:
        raise ValueError("Decimal odds must be > 1.0.")
    return 1.0 / decimal_odds


def expected_value_per_dollar(win_prob: float, decimal_odds: float) -> float:
    if not (0.0 <= win_prob <= 1.0):
        raise ValueError("Win probability must be between 0 and 1.")
    profit = decimal_odds - 1.0
    return (win_prob * profit) - ((1.0 - win_prob) * 1.0)


def parse_american_odds(s: str) -> int:
    s = s.strip()
    if s.startswith("+"):
        s = s[1:]
    return int(s)


def decision_label(ev: float) -> str:
    if ev > 0:
        return "+EV"
    if ev < 0:
        return "-EV"
    return "EV=0"


def safe_float(s: str) -> float:
    return float(s.strip())


def process_row(row: dict) -> dict:
    bet_name = (row.get("bet_name") or "").strip() or "Unnamed"
    american_raw = (row.get("american_odds") or "").strip()
    win_prob_raw = (row.get("win_prob") or "").strip()

    american = parse_american_odds(american_raw)
    win_prob = safe_float(win_prob_raw)

    dec = american_to_decimal(american)
    implied = decimal_to_implied_prob(dec)
    ev = expected_value_per_dollar(win_prob, dec)

    return {
        "bet_name": bet_name,
        "american_odds": american,
        "win_prob": win_prob,
        "decimal_odds": round(dec, 4),
        "implied_prob": round(implied, 4),
        "ev_per_1": round(ev, 4),
        "decision": decision_label(ev),
    }


def main(input_csv: str = "bets.csv", output_csv: str = "results.csv") -> None:
    rows_out = []
    errors = 0

    with open(input_csv, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"bet_name", "american_odds", "win_prob"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                f"Input CSV must have headers: {sorted(required)}. "
                f"Found: {reader.fieldnames}"
            )

        for i, row in enumerate(reader, start=2):  # header is line 1
            try:
                rows_out.append(process_row(row))
            except Exception as e:
                errors += 1
                rows_out.append({
                    "bet_name": (row.get("bet_name") or "").strip() or f"Row{i}",
                    "american_odds": row.get("american_odds", ""),
                    "win_prob": row.get("win_prob", ""),
                    "decimal_odds": "",
                    "implied_prob": "",
                    "ev_per_1": "",
                    "decision": f"ERROR: {e}",
                })

    fieldnames = ["bet_name", "american_odds", "win_prob", "decimal_odds", "implied_prob", "ev_per_1", "decision"]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"Done. Wrote {len(rows_out)} rows to {output_csv}. Errors: {errors}")


if __name__ == "__main__":
    main()
