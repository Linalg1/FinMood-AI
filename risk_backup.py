"""Transparent illustrative cash-flow-at-risk simulation; not a credit score."""
from datetime import date, timedelta
import numpy as np


def forecast(balance: float, expenses: list[dict], *, horizon: int = 30,
             simulations: int = 10000, reserve: float = 200.0,
             monthly_income: float = 0.0, spending_multiplier: float = 1.0,
             seed: int = 42, today: date | None = None) -> dict:
    if balance < 0 or reserve < 0 or monthly_income < 0 or spending_multiplier < 0:
        raise ValueError('Balance, reserve, monthly income and multiplier must be nonnegative')
    if not 1 <= horizon <= 365 or not 100 <= simulations <= 100000:
        raise ValueError('Horizon must be 1-365 days and simulations 100-100000')
    today = today or date.today()
    # Daily totals, including days without expenses, for an inclusive 60-day lookback.
    start = today - timedelta(days=59)
    totals = {start + timedelta(days=i): 0.0 for i in range(60)}
    for item in expenses:
        d = date.fromisoformat(item['date'])
        amount = float(item['amount'])
        if amount < 0:
            raise ValueError('Expenses must not be negative')
        if d in totals:
            totals[d] += amount
    daily = np.array(list(totals.values()), dtype=float)
    rng = np.random.default_rng(seed)
    draws = rng.choice(daily, size=(simulations, horizon), replace=True) * spending_multiplier
    projected_dates = [today + timedelta(days=i+1) for i in range(horizon)]
    income = np.array([monthly_income if d.day == 1 else 0.0 for d in projected_dates])
    paths = balance + np.cumsum(income[None, :] - draws, axis=1)
    ending = paths[:, -1]
    breaches = (paths < reserve).any(axis=1)
    return {
        'opening_balance': round(balance, 2),
        'expected_ending_balance': round(float(np.mean(ending)), 2),
        'median_ending_balance': round(float(np.median(ending)), 2),
        'p05_ending_balance': round(float(np.percentile(ending, 5)), 2),
        'p95_ending_balance': round(float(np.percentile(ending, 95)), 2),
        'probability_reserve_breach': round(float(np.mean(breaches)), 4),
        'daily_spend_mean': round(float(np.mean(daily)), 2),
        'sample_expense_days': int(np.count_nonzero(daily)),
        'horizon_days': horizon,
        'simulations': simulations,
        'model': '60-day empirical daily-spend bootstrap; fixed monthly income on day 1',
        'limitations': 'Demo estimate: assumes future days resemble the last 60 days, ignores inflation, trends and irregular bills. Mood is not used to score financial risk.',
        'dates': [d.isoformat() for d in projected_dates],
        'mean_path': [round(float(v), 2) for v in np.mean(paths, axis=0)],
        'p05_path': [round(float(v), 2) for v in np.percentile(paths, 5, axis=0)],
        'p95_path': [round(float(v), 2) for v in np.percentile(paths, 95, axis=0)],
    }
