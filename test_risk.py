from datetime import date
from risk import forecast


def test_zero_expenses_gives_no_breach():
    out = forecast(1000, [], monthly_income=0, reserve=200, today=date(2026, 10, 18), simulations=100)
    assert out['expected_ending_balance'] == 1000
    assert out['probability_reserve_breach'] == 0


def test_reproducible_and_scenario_improves():
    expenses = [{'date': '2026-10-18', 'amount': 45}]
    kw = dict(today=date(2026, 10, 18), simulations=2000, reserve=70)
    base = forecast(100, expenses, **kw)
    assert base == forecast(100, expenses, **kw)
    improved = forecast(100, expenses, spending_multiplier=0, **kw)
    assert improved['probability_reserve_breach'] <= base['probability_reserve_breach']


def test_monthly_income_first_of_month():
    out = forecast(100, [], today=date(2026, 10, 30), horizon=3, monthly_income=500, simulations=100)
    assert out['expected_ending_balance'] == 600
