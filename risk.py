"""
FinMood AI — Quantitative Liquidity Risk Engine V2

Monte Carlo cash-flow simulation using historical bootstrapping.

Features:
- Cash-flow forecasting
- Liquidity-at-Risk (LaR)
- Expected Shortfall (ES)
- Reserve-breach probability
- Spending stress scenarios

For educational and demonstration purposes.
Not a credit score or financial recommendation.
"""

from datetime import date, timedelta

import numpy as np


def forecast(
    balance: float,
    expenses: list[dict],
    *,
    horizon: int = 30,
    simulations: int = 10000,
    reserve: float = 200.0,
    monthly_income: float = 0.0,
    spending_multiplier: float = 1.0,
    seed: int = 42,
    today: date | None = None,
    lookback_days: int = 180,
) -> dict:

    # -----------------------------------------
    # 1. Validate inputs
    # -----------------------------------------

    financial_inputs = [
        balance,
        reserve,
        monthly_income,
        spending_multiplier,
    ]

    if not all(np.isfinite(value) for value in financial_inputs):
        raise ValueError("Financial inputs must be finite numbers")

    if any(value < 0 for value in financial_inputs):
        raise ValueError("Financial inputs must be nonnegative")

    if not 1 <= horizon <= 365:
        raise ValueError("Horizon must be between 1 and 365 days")

    if not 100 <= simulations <= 100000:
        raise ValueError(
            "Simulations must be between 100 and 100000"
        )

    if not 1 <= lookback_days <= 365:
        raise ValueError(
            "Lookback must be between 1 and 365 days"
        )

    today = today or date.today()

    # -----------------------------------------
    # 2. Prepare historical spending data
    # -----------------------------------------

    start = today - timedelta(days=lookback_days - 1)

    totals = {
        start + timedelta(days=i): 0.0
        for i in range(lookback_days)
    }

    for item in expenses:

        transaction_date = date.fromisoformat(item["date"])

        amount = float(item["amount"])

        if not np.isfinite(amount) or amount < 0:
            raise ValueError(
                "Expense amounts must be finite and nonnegative"
            )

        if transaction_date in totals:
            totals[transaction_date] += amount

    daily = np.array(
        list(totals.values()),
        dtype=float,
    )

    sample_expense_days = int(np.count_nonzero(daily))

    # -----------------------------------------
    # 3. Monte Carlo simulation
    # -----------------------------------------

    rng = np.random.default_rng(seed)

    simulated_expenses = rng.choice(
        daily,
        size=(simulations, horizon),
        replace=True,
    )

    simulated_expenses *= spending_multiplier

    # -----------------------------------------
    # 4. Project future income
    # -----------------------------------------

    projected_dates = [
        today + timedelta(days=i + 1)
        for i in range(horizon)
    ]

    income = np.array([
        monthly_income if day.day == 1 else 0.0
        for day in projected_dates
    ])

    # -----------------------------------------
    # 5. Calculate simulated cash balances
    # -----------------------------------------

    net_cashflows = (
        income[None, :] - simulated_expenses
    )

    paths = balance + np.cumsum(
        net_cashflows,
        axis=1,
    )

    ending_balances = paths[:, -1]

    # -----------------------------------------
    # 6. Reserve-breach probability
    # -----------------------------------------

    breaches = (paths < reserve).any(axis=1)

    breach_probability = float(np.mean(breaches))

    # -----------------------------------------
    # 7. Liquidity-at-Risk (95%)
    # -----------------------------------------

    # Positive losses represent a decline in cash
    # relative to the opening balance.
    #
    # Gains produce negative losses.

    net_losses = balance - ending_balances

    loss_quantile_95 = float(
        np.percentile(net_losses, 95)
    )

    # Report an adverse cash deterioration,
    # floored at zero.
    liquidity_at_risk_95 = max(
        0.0,
        loss_quantile_95,
    )

    # -----------------------------------------
    # 8. Expected Shortfall (95%)
    # -----------------------------------------

    # Average net loss among the worst 5%
    # of simulated outcomes, including ties.

    tail_losses = net_losses[
        net_losses >= loss_quantile_95
    ]

    expected_shortfall_95 = max(
        0.0,
        float(np.mean(tail_losses)),
    )

    # -----------------------------------------
    # 9. Risk diagnostics
    # -----------------------------------------

    expected_balance = float(
        np.mean(ending_balances)
    )

    median_balance = float(
        np.median(ending_balances)
    )

    balance_volatility = float(
        np.std(ending_balances, ddof=1)
    )

    worst_ending_balance = float(
        np.min(ending_balances)
    )

    # Monte Carlo sampling error approximation
    # for the estimated breach probability.

    breach_standard_error = float(
        np.sqrt(
            breach_probability
            * (1 - breach_probability)
            / simulations
        )
    )

    # -----------------------------------------
    # 10. Return results
    # -----------------------------------------

    return {

        # Existing dashboard/API fields

        "opening_balance": round(balance, 2),

        "expected_ending_balance": round(
            expected_balance, 2
        ),

        "median_ending_balance": round(
            median_balance, 2
        ),

        "p05_ending_balance": round(
            float(np.percentile(ending_balances, 5)),
            2,
        ),

        "p95_ending_balance": round(
            float(np.percentile(ending_balances, 95)),
            2,
        ),

        "probability_reserve_breach": round(
            breach_probability, 4
        ),

        "daily_spend_mean": round(
            float(np.mean(daily)), 2
        ),

        "sample_expense_days": sample_expense_days,

        "horizon_days": horizon,

        "simulations": simulations,

        # New quantitative risk metrics

        "liquidity_at_risk_95": round(
            liquidity_at_risk_95, 2
        ),

        "expected_shortfall_95": round(
            expected_shortfall_95, 2
        ),

        "ending_balance_volatility": round(
            balance_volatility, 2
        ),

        "worst_simulated_ending_balance": round(
            worst_ending_balance, 2
        ),

        "reserve_breach_standard_error": round(
            breach_standard_error, 6
        ),

        "lookback_days": lookback_days,

        # Model documentation

        "model": (
            f"{lookback_days}-day empirical "
            "daily-spend bootstrap; "
            "fixed monthly income on day 1"
        ),

        "limitations": (
            "Illustrative model. Assumes independent "
            "daily spending drawn from historical data. "
            "Does not separately model inflation, trends, "
            "recurring bills or income uncertainty. "
            "Liquidity-at-Risk and Expected Shortfall "
            "measure simulated net cash deterioration "
            "relative to opening balance, floored at zero. "
            "Mood is not used to score financial risk."
        ),

        # Chart data

        "dates": [
            day.isoformat()
            for day in projected_dates
        ],

        "mean_path": [
            round(float(value), 2)
            for value in np.mean(paths, axis=0)
        ],

        "p05_path": [
            round(float(value), 2)
            for value in np.percentile(
                paths, 5, axis=0
            )
        ],

        "p95_path": [
            round(float(value), 2)
            for value in np.percentile(
                paths, 95, axis=0
            )
        ],
    }