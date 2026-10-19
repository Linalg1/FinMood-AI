"""
FinMood AI - MCP Server

Connects conversational AI clients to:
- Expense tracking
- Mood check-ins
- Monte Carlo cash-flow forecasting
- Financial stress testing

Local development prototype.
"""

from mcp.server.fastmcp import FastMCP

from storage import (
    add_expense,
    add_mood,
    get_expenses,
)

from risk import forecast


# Create the MCP server.
# Use port 8001 because FastAPI already uses 8000.

mcp = FastMCP(
    "FinMood AI",
    host="127.0.0.1",
    port=8001,
    json_response=True,
)


# ---------------------------------------
# TOOL 1: Record an expense
# ---------------------------------------

@mcp.tool()
def log_expense(
    amount: float,
    category: str,
    note: str = "",
) -> dict:
    """
    Record an expense in the FinMood database.

    Only use this tool when the user explicitly
    requests or confirms recording an expense.
    """

    allowed_categories = [
        "Food",
        "Transport",
        "Shopping",
        "Bills",
        "Other",
    ]

    if amount <= 0 or amount > 100000:
        raise ValueError("Invalid expense amount")

    if category not in allowed_categories:
        raise ValueError(
            f"Category must be one of {allowed_categories}"
        )

    if len(note) > 500:
        raise ValueError("Note is too long")

    add_expense(
        amount=amount,
        category=category,
        note=note,
    )

    return {
        "success": True,
        "message": "Expense recorded successfully",
        "amount": amount,
        "category": category,
    }


# ---------------------------------------
# TOOL 2: Record an optional mood
# ---------------------------------------

@mcp.tool()
def record_mood(
    mood: str,
    note: str = "",
) -> dict:
    """
    Record a voluntary emotional check-in.

    Ask for the user's confirmation before
    storing sensitive emotional information.
    """

    allowed_moods = [
        "Happy",
        "Calm",
        "Neutral",
        "Stressed",
        "Sad",
        "Anxious",
    ]

    if mood not in allowed_moods:
        raise ValueError("Unsupported mood")

    if len(note) > 500:
        raise ValueError("Note is too long")

    add_mood(
        mood=mood,
        note=note,
    )

    return {
        "success": True,
        "message": "Mood check-in recorded",
        "mood": mood,
    }


# ---------------------------------------
# TOOL 3: Financial risk forecast
# ---------------------------------------

@mcp.tool()
def forecast_cashflow(
    balance: float,
    monthly_income: float = 2200.0,
    reserve: float = 200.0,
    horizon: int = 30,
) -> dict:
    """
    Simulate future cash balances using
    Monte Carlo historical bootstrapping.

    Returns liquidity risk metrics.
    """

    expenses = get_expenses()

    result = forecast(
        balance=balance,
        expenses=expenses,
        monthly_income=monthly_income,
        reserve=reserve,
        horizon=horizon,
        simulations=10000,
        lookback_days=180,
    )

    return {
        "expected_ending_balance":
            result["expected_ending_balance"],

        "probability_reserve_breach":
            result["probability_reserve_breach"],

        "liquidity_at_risk_95":
            result["liquidity_at_risk_95"],

        "expected_shortfall_95":
            result["expected_shortfall_95"],

        "ending_balance_volatility":
            result["ending_balance_volatility"],

        "simulations":
            result["simulations"],

        "model":
            result["model"],

        "limitations":
            result["limitations"],
    }


# ---------------------------------------
# TOOL 4: Financial stress testing
# ---------------------------------------

@mcp.tool()
def simulate_financial_stress(
    balance: float,
    monthly_income: float = 2200.0,
    reserve: float = 200.0,
    spending_increase_percent: float = 20.0,
    horizon: int = 30,
) -> dict:
    """
    Compare baseline cash-flow risk against
    a hypothetical spending increase.
    """

    if not 0 <= spending_increase_percent <= 200:
        raise ValueError(
            "Spending increase must be between 0 and 200%"
        )

    expenses = get_expenses()

    baseline = forecast(
        balance=balance,
        expenses=expenses,
        monthly_income=monthly_income,
        reserve=reserve,
        horizon=horizon,
        lookback_days=180,
    )

    stressed = forecast(
        balance=balance,
        expenses=expenses,
        monthly_income=monthly_income,
        reserve=reserve,
        horizon=horizon,
        spending_multiplier=(
            1 + spending_increase_percent / 100
        ),
        lookback_days=180,
    )

    return {
        "spending_increase_percent":
            spending_increase_percent,

        "baseline_ending_balance":
            baseline["expected_ending_balance"],

        "stressed_ending_balance":
            stressed["expected_ending_balance"],

        "baseline_breach_probability":
            baseline["probability_reserve_breach"],

        "stressed_breach_probability":
            stressed["probability_reserve_breach"],

        "baseline_expected_shortfall":
            baseline["expected_shortfall_95"],

        "stressed_expected_shortfall":
            stressed["expected_shortfall_95"],
    }


# ---------------------------------------
# Start MCP server
# ---------------------------------------

if __name__ == "__main__":
    mcp.run(transport="streamable-http")