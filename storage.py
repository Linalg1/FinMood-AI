"""Local-only SQLite demo data storage."""
import sqlite3
from pathlib import Path
from datetime import date, timedelta
import random

DB = Path(__file__).resolve().parent / 'finmood.sqlite3'


def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.execute('CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, date TEXT NOT NULL, amount REAL NOT NULL CHECK(amount >= 0), category TEXT NOT NULL, note TEXT NOT NULL DEFAULT "")')
    db.execute('CREATE TABLE IF NOT EXISTS moods (id INTEGER PRIMARY KEY, date TEXT NOT NULL, mood TEXT NOT NULL, note TEXT NOT NULL DEFAULT "")')
    db.commit()
    return db


def add_expense(amount, category, note='', day=None):
    if not 0 < float(amount) <= 1000000:
        raise ValueError('Expense must be positive and at most 1,000,000')
    with connect() as db:
        db.execute('INSERT INTO expenses(date, amount, category, note) VALUES (?, ?, ?, ?)', (str(day or date.today()), float(amount), str(category)[:60], str(note)[:200]))


def add_mood(mood, note='', day=None):
    if mood not in {'Happy', 'Calm', 'Neutral', 'Stressed', 'Sad', 'Anxious'}:
        raise ValueError('Choose one of the supported moods')
    with connect() as db:
        db.execute('INSERT INTO moods(date, mood, note) VALUES (?, ?, ?)', (str(day or date.today()), mood, str(note)[:200]))


def get_expenses():
    with connect() as db:
        return [dict(r) for r in db.execute('SELECT * FROM expenses ORDER BY date DESC, id DESC')]


def get_moods():
    with connect() as db:
        return [dict(r) for r in db.execute('SELECT * FROM moods ORDER BY date DESC, id DESC')]


def seed_demo():
    with connect() as db:
        if db.execute('SELECT COUNT(*) FROM expenses').fetchone()[0]:
            return False
    rng = random.Random(12)
    for i in range(60):
        day = date.today() - timedelta(days=i)
        for category, probability, low, high in [('Food', .80, 5, 22), ('Transport', .40, 3, 15), ('Shopping', .17, 15, 90), ('Bills', .08, 25, 75)]:
            if rng.random() < probability:
                add_expense(round(rng.uniform(low, high), 2), category, day=day)
        if i % 3 == 0:
            add_mood(rng.choice(['Happy', 'Calm', 'Neutral', 'Stressed', 'Anxious']), day=day)
    return True
