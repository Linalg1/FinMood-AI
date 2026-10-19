"""API tool interface intended for future MCP / Alexa+ adaptation; not itself an MCP server."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from storage import add_expense, add_mood, get_expenses, get_moods
from risk import forecast

app = FastAPI(title='FinMood AI API', version='0.1.0')


class Expense(BaseModel):
    amount: float = Field(gt=0, le=1000000)
    category: str = Field(min_length=1, max_length=60)
    note: str = Field(default='', max_length=200)


class Mood(BaseModel):
    mood: str
    note: str = Field(default='', max_length=200)


class Scenario(BaseModel):
    balance: float = Field(default=1800, ge=0)
    monthly_income: float = Field(default=2200, ge=0)
    reserve: float = Field(default=200, ge=0)
    horizon: int = Field(default=30, ge=1, le=365)
    spending_multiplier: float = Field(default=1.0, ge=0, le=5)


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.get('/expenses')
def expenses():
    return get_expenses()


@app.post('/expenses')
def log_expense(item: Expense):
    add_expense(item.amount, item.category, item.note)
    return {'message': 'Expense saved', 'amount': item.amount, 'category': item.category}


@app.get('/moods')
def moods():
    return get_moods()


@app.post('/moods')
def log_mood(item: Mood):
    try:
        add_mood(item.mood, item.note)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    return {'message': 'Optional mood check-in saved'}


@app.post('/risk/forecast')
def calculate_risk(scenario: Scenario):
    return forecast(scenario.balance, get_expenses(), monthly_income=scenario.monthly_income,
                    reserve=scenario.reserve, horizon=scenario.horizon,
                    spending_multiplier=scenario.spending_multiplier)
