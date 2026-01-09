def american_to_decimal(american: int) -> float:
    """
    Convert American odds to Decimal odds.
    Example: -110 -> 1.9091..., +150 -> 2.50
    """
    if american == 0:
        raise ValueError("American odds cannot be 0.")
    if american > 0:
        return 1.0 + (american / 100.0)
    return 1.0 + (100.0 / abs(american))


def decimal_to_implied_prob(decimal_odds: float) -> float:
    """
    Convert decimal odds to implied probability.
    Example: 2.00 -> 0.50
    """
    if decimal_odds <= 1.0:
        raise ValueError("Decimal odds must be > 1.0.")
    return 1.0 / decimal_odds


def expected_value_per_dollar(win_prob: float, decimal_odds: float) -> float:
    """
    EV per $1 staked:
    EV = p*(profit) - (1-p)*1
    profit per $1 stake at decimal odds = (decimal_odds - 1)
    """
    if not (0.0 <= win_prob <= 1.0):
        raise ValueError("Win probability must be between 0 and 1.")
    profit = decimal_odds - 1.0
    return (win_prob * profit) - ((1.0 - win_prob) * 1.0)


def main() -> None:
    print("Odds + EV Calculator (American odds)")
    print("-----------------------------------")

    american_str = input("Enter American odds (e.g., -110 or 150): ").strip()
    winprob_str = input("Enter your win probability (0 to 1, e.g., 0.55): ").strip()

    try:
        american = int(american_str)
        win_prob = float(winprob_str)

        dec = american_to_decimal(american)
        implied = decimal_to_implied_prob(dec)
        ev = expected_value_per_dollar(win_prob, dec)

        print("\nResults")
        print("-------")
        print(f"American odds: {american}")
        print(f"Decimal odds: {dec:.4f}")
        print(f"Implied probability: {implied:.4f} ({implied*100:.2f}%)")
        print(f"Your win probability: {win_prob:.4f} ({win_prob*100:.2f}%)")
        print(f"EV per $1 staked: {ev:.4f}")

        if ev > 0:
            print("Decision: +EV (good price) ✅")
        elif ev < 0:
            print("Decision: -EV (bad price) ❌")
        else:
            print("Decision: Break-even ⚖️")

    except ValueError as e:
        print(f"\nError: {e}")
        print("Tip: odds must be an integer like -110 or 150; win prob must be 0 to 1.")


if __name__ == "__main__":
    main()
