from datetime import date

from risk import forecast


def test_simulation_is_reproducible():

    expenses = [
        {
            "date": "2026-10-01",
            "amount": 50.0,
        },
        {
            "date": "2026-10-02",
            "amount": 20.0,
        },
    ]

    result1 = forecast(
        balance=1000,
        expenses=expenses,
        today=date(2026, 10, 18),
        seed=42,
    )

    result2 = forecast(
        balance=1000,
        expenses=expenses,
        today=date(2026, 10, 18),
        seed=42,
    )

    assert result1 == result2


def test_expected_shortfall():

    expenses = [
        {
            "date": "2026-10-01",
            "amount": 100.0,
        },
        {
            "date": "2026-10-02",
            "amount": 250.0,
        },
    ]

    result = forecast(
        balance=500,
        expenses=expenses,
        horizon=30,
        simulations=10000,
        today=date(2026, 10, 18),
    )

    assert (
        result["expected_shortfall_95"]
        >= result["liquidity_at_risk_95"]
    )


def test_more_spending_increases_risk():

    expenses = [
        {
            "date": "2026-10-01",
            "amount": 100.0,
        }
    ]

    baseline = forecast(
        balance=500,
        expenses=expenses,
        spending_multiplier=1.0,
        today=date(2026, 10, 18),
    )

    stressed = forecast(
        balance=500,
        expenses=expenses,
        spending_multiplier=2.0,
        today=date(2026, 10, 18),
    )

    assert (
        stressed["probability_reserve_breach"]
        >= baseline["probability_reserve_breach"]
    )

    assert (
        stressed["expected_ending_balance"]
        <= baseline["expected_ending_balance"]
    )