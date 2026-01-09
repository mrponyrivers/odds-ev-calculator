import csv


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


def kelly_fraction(win_prob: float, decimal_odds: float) -> float:
    if decimal_odds <= 1.0:
        return 0.0
    f = (win_prob * decimal_odds - 1.0) / (decimal_odds - 1.0)
    return max(0.0, f)


def parse_american_odds(s: str) -> int:
    s = s.strip()
    if s.startswith("+"):
        s = s[1:]
    return int(s)


def compute_row(bet_name: str, american_odds: int, win_prob: float) -> dict:
    dec = american_to_decimal(american_odds)
    implied = decimal_to_implied_prob(dec)
    ev = expected_value_per_dollar(win_prob, dec)
    edge = win_prob - implied
    return {
        "bet_name": bet_name,
        "american_odds": american_odds,
        "win_prob": round(win_prob, 4),
        "decimal_odds": round(dec, 4),
        "implied_prob": round(implied, 4),
        "edge": round(edge, 4),
        "ev_per_1": round(ev, 4),
    }


def read_bets_csv(path: str) -> list:
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"bet_name", "american_odds", "win_prob"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(
                f"Input CSV must have headers: {sorted(required)}. Found: {reader.fieldnames}"
            )
        return list(reader)


def write_csv(path: str, fieldnames: list, rows: list) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
