from ollama import chat

print("Connecting to Qwen3...", flush=True)

response = chat(
    model="qwen3:0.6b",
    messages=[
        {
            "role": "system",
            "content": (
                "You are FinMood AI, a financial wellness assistant. "
                "Identify financial transactions and emotional states. "
                "Never assume that a negated emotion is positive."
            ),
        },
        {
            "role": "user",
            "content": (
                "I bought 100 euros of clothes yesterday "
                "and I'm not feeling happy today."
            ),
        },
    ],
    think=False,
    options={
        "temperature": 0,
        "num_ctx": 2048,
        "num_predict": 200,
    },
)

print("\n=== MODEL RESPONSE ===")
print(repr(response.message.content))

print("\n=== THINKING ===")
print(repr(response.message.thinking))

print("\n=== DONE ===")