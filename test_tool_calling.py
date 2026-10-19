from ollama import chat

tools = [
    {
        "type": "function",
        "function": {
            "name": "log_expense",
            "description": (
                "Prepare a financial expense for recording. "
                "The user must confirm before it is saved."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "Expense amount in euros"
                    },
                    "category": {
                        "type": "string",
                        "enum": [
                            "Food",
                            "Transport",
                            "Shopping",
                            "Bills",
                            "Other"
                        ]
                    }
                },
                "required": ["amount", "category"]
            }
        }
    }
]

response = chat(
    model="qwen3:0.6b",
    messages=[
        {
            "role": "system",
            "content": (
                "You are FinMood AI, a financial assistant. "
                "Your task is to select tools. "
                "When the user reports a purchase, "
                "you MUST call log_expense with the amount "
                "and category. "
                "Clothing purchases belong to Shopping. "
                "Do not answer in plain text when a tool applies. "
                "The tool call only prepares an action; "
                "the application will request confirmation "
                "before saving anything."
            ),
        },
        {
            "role": "user",
            "content": "I just bought 100 euros of clothes.",
        },
    ],
    tools=tools,
    think=False,
    options={
        "temperature": 0,
        "num_ctx": 4096,
        "num_predict": 300,
    },
)

print("\n=== MODEL RESPONSE ===")
print(repr(response.message.content))

print("\n=== TOOL CALLS ===")
print(response.message.tool_calls)

print("\n=== FINISH REASON ===")
print(response.done_reason)