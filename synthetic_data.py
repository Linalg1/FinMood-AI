import random
from datetime import date, timedelta

from storage import add_expense, add_mood


def generate_synthetic_data(days=180):

    random_generator = random.Random(42)

    categories = {
        "Food": (0.85, 5, 30),
        "Transport": (0.65, 2, 15),
        "Shopping": (0.25, 10, 100),
        "Bills": (0.10, 20, 80),
    }

    moods = [
        "Happy",
        "Calm",
        "Neutral",
        "Stressed",
        "Anxious",
    ]

    today = date.today()

    for i in range(days):

        current_day = today - timedelta(days=i)

        for category, parameters in categories.items():

            probability, minimum, maximum = parameters

            if random_generator.random() < probability:

                amount = round(
                    random_generator.uniform(minimum, maximum),
                    2
                )

                add_expense(
                    amount=amount,
                    category=category,
                    note="Synthetic demo transaction",
                    day=current_day
                )

        # Occasionally simulate an unexpected expense
        if random_generator.random() < 0.03:

            unexpected_amount = round(
                random_generator.uniform(100, 400),
                2
            )

            add_expense(
                amount=unexpected_amount,
                category="Other",
                note="Synthetic unexpected expense",
                day=current_day
            )

        # Optional synthetic mood check-in
        if random_generator.random() < 0.75:

            mood = random_generator.choice(moods)

            add_mood(
                mood=mood,
                note="Synthetic demo mood",
                day=current_day
            )

    print(f"Generated {days} days of synthetic data!")


if __name__ == "__main__":
    generate_synthetic_data()