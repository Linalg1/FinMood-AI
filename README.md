# FinMood AI — Quantitative Financial Wellness Prototype

**Status:** Working local prototype. **Not yet connected to Alexa+ or MCP.** Uses local SQLite and optional mood entries. No bank credentials or external services required.

## Getting started

Requires Python 3.10+ (3.11 or 3.12 recommended).

```bash
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

In the app, click **Load synthetic demo data**, then inspect the dashboard. The data is generated locally and contains no real customer information. The example input for current balance is a scenario assumption, not a bank account connection.

## API (separate terminal)

```bash
uvicorn api:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation. You can POST an expense to `/expenses`, an optional mood to `/moods`, and a scenario to `/risk/forecast`.

Example risk request:

```json
{"balance":1800,"monthly_income":2200,"reserve":200,"horizon":30,"spending_multiplier":1.0}
```

## Test

```bash
pytest -q
```

## Model notes

Monte Carlo bootstrap: sample daily expense totals from a 60-day lookback (including zero-spend days), simulate 10,000 scenarios over 30 days, and add assumed monthly income on the first day of the month. Reserve breach is the fraction of paths that dip below the threshold **at any time**, not the chance of negative month-end balance. Ending balance 5th percentile illustrates a downside scenario, not market VaR.

This is an educational demonstration, not financial advice, a validated financial forecast, or a creditworthiness assessment. Irregular costs, trends, income uncertainty, seasonality, and time dependence are not yet modeled. Mood notes are never used for financial scoring. Data remains in a local SQLite file `finmood.sqlite3`, which must not be committed or publicly uploaded. Delete that file to erase local demo data.

## Alexa+ integration plan

The REST API is a foundation only. Next: wrap the endpoint operations as proper MCP tools with the transport required by the hackathon or implement the supported Alexa+ pathway, then demonstrate real tool calls. Do not claim the prototype is already an Alexa+ app.
# FinMood-AI
