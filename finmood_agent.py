import asyncio
import json
import math

from ollama import chat
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


MODEL = "qwen3:0.6b"
MCP_URL = "http://127.0.0.1:8001/mcp"

WRITE_TOOLS = {"log_expense", "record_mood"}

ALLOWED_CATEGORIES = {
    "Food", "Transport", "Shopping", "Bills", "Other"
}

ALLOWED_MOODS = {
    "Happy", "Calm", "Neutral",
    "Stressed", "Sad", "Anxious"
}

SYSTEM_PROMPT = """
You are FinMood AI, a conversational financial wellness assistant.

Use tools when the user asks to:
- Record an expense
- Record an optional mood check-in
- Forecast cash flow or financial risk
- Simulate a spending stress scenario

Always select the appropriate tool when possible.

Clothing purchases belong to Shopping.
Do not interpret "not happy" as Happy.

Never claim an expense or mood was recorded until
the application confirms that the tool succeeded.

Financial figures must come from the risk tools.
Do not invent probabilities or risk metrics.

The application requires explicit confirmation
before executing tools that save information.
"""


async def execute_mcp_tool(name, arguments):
    """Execute a tool through the real MCP server."""

    async with streamablehttp_client(MCP_URL) as (
        read, write, _
    ):
        async with ClientSession(read, write) as session:
            await session.initialize()

            response = await session.call_tool(
                name,
                arguments=arguments,
            )

            if response.isError:
                raise RuntimeError("MCP tool execution failed")

            if response.structuredContent is not None:
                data = response.structuredContent
                if isinstance(data, dict) and set(data) == {"result"}:
                    return data["result"]
                return data

            for item in response.content:
                if item.type == "text":
                    return json.loads(item.text)

            raise RuntimeError("No MCP result returned")


async def get_mcp_tools():
    """Discover tool definitions from our MCP server."""

    async with streamablehttp_client(MCP_URL) as (
        read, write, _
    ):
        async with ClientSession(read, write) as session:
            await session.initialize()
            response = await session.list_tools()

            return [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema,
                    },
                }
                for tool in response.tools
            ]


def validate_arguments(name, arguments):
    """Validate model-generated arguments before execution."""

    if name == "log_expense":
        amount = float(arguments["amount"])

        if not math.isfinite(amount) or not 0 < amount <= 100000:
            raise ValueError("Invalid expense amount")

        if arguments["category"] not in ALLOWED_CATEGORIES:
            raise ValueError("Invalid expense category")

        return {
            "amount": amount,
            "category": arguments["category"],
            "note": str(arguments.get("note", ""))[:500],
        }

    if name == "record_mood":
        mood = arguments["mood"]

        if mood not in ALLOWED_MOODS:
            raise ValueError("Invalid mood")

        return {
            "mood": mood,
            "note": str(arguments.get("note", ""))[:500],
        }

    if name in {"forecast_cashflow", "simulate_financial_stress"}:
        # Read-only operations still need server-side validation.
        # Use validated application defaults where appropriate.
        return arguments

    raise ValueError(f"Tool not allowed: {name}")


def interpret_message(message, tools):
    """Ask Qwen3 to select an MCP tool."""

    response = chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        tools=tools,
        think=False,
        options={
            "temperature": 0,
            "num_ctx": 4096,
            "num_predict": 300,
        },
    )

    calls = response.message.tool_calls or []

    if calls:
        call = calls[0]

        name = call.function.name
        arguments = validate_arguments(
            name,
            call.function.arguments,
        )

        return {
            "type": "tool_request",
            "tool": name,
            "arguments": arguments,
            "requires_confirmation": name in WRITE_TOOLS,
        }

    return {
        "type": "message",
        "content": response.message.content
        or "Could you rephrase your request?",
    }


async def process_message(message):
    """Interpret a message and execute read-only tools."""

    tools = await get_mcp_tools()

    decision = interpret_message(message, tools)

    if decision["type"] == "message":
        return decision

    if decision["requires_confirmation"]:
        return decision

    result = await execute_mcp_tool(
        decision["tool"],
        decision["arguments"],
    )

    return {
        "type": "tool_result",
        "tool": decision["tool"],
        "result": result,
    }


if __name__ == "__main__":
    print("FinMood AI Agent")

    while True:
        message = input("\nYou: ").strip()

        if message.lower() in {"exit", "quit"}:
            break

        try:
            result = asyncio.run(process_message(message))
            print(json.dumps(result, indent=2))
        except Exception as error:
            print(f"Error: {error}")