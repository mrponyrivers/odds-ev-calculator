from odds_ev_tool.core import american_to_decimal, expected_value_per_dollar


def test_american_to_decimal_minus_110():
    assert round(american_to_decimal(-110), 4) == 1.9091


def test_ev_positive_example():
    dec = american_to_decimal(-110)
    assert expected_value_per_dollar(0.55, dec) > 0


if __name__ == "__main__":
    test_american_to_decimal_minus_110()
    test_ev_positive_example()
    print("Tests passed ✅")
