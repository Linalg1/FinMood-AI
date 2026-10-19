import asyncio
import json
import re

import streamlit as st
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


MCP_URL = "http://127.0.0.1:8001/mcp"

st.set_page_config(
    page_title="FinMood AI — Alexa+ Simulation",
    page_icon="💠",
)

st.title("💠 FinMood AI")
st.caption(
    "Alexa+-style simulation powered by a real MCP server. "
    "Not connected to Amazon Alexa+."
)


async def call_tool(name, arguments):
    async with streamablehttp_client(MCP_URL) as (
        read, write, _
    ):
        async with ClientSession(read, write) as session:
            await session.initialize()

            response = await session.call_tool(
                name,
                arguments=arguments
            )

            if response.isError:
                raise RuntimeError(
                    "MCP tool returned an error"
                )

            if response.structuredContent is not None:
                data = response.structuredContent

                if isinstance(data, dict) and set(data) == {"result"}:
                    return data["result"]

                return data

            for item in response.content:
                if item.type == "text":
                    return json.loads(item.text)

            raise RuntimeError("Empty MCP response")


# Financial scenario settings

with st.sidebar:
    st.header("Financial settings")

    balance = st.number_input(
        "Current balance (€)",
        min_value=0.0,
        value=1800.0,
    )

    income = st.number_input(
        "Monthly income (€)",
        min_value=0.0,
        value=2200.0,
    )

    reserve = st.number_input(
        "Cash reserve (€)",
        min_value=0.0,
        value=200.0,
    )


# Conversation history

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_action" not in st.session_state:
    st.session_state.pending_action = None


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Chat interface

prompt = st.chat_input(
    "Ask FinMood about your finances or mood..."
)

if prompt:

    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
    })

    with st.chat_message("user"):
        st.write(prompt)

    text = prompt.lower().strip()
    reply = ""

    try:
        pending = st.session_state.pending_action

        # Confirm or cancel a pending write operation
        if pending is not None:
            if text in {"yes", "confirm", "save it"}:
                result = asyncio.run(
                    call_tool(
                        pending["tool"],
                        pending["arguments"]
                    )
                )

                reply = result.get(
                    "message",
                    "Your entry was saved."
                )

                st.session_state.pending_action = None

            elif text in {"no", "cancel"}:
                st.session_state.pending_action = None
                reply = "Okay, I won't save that."

            else:
                reply = (
                    "Please answer yes or no to confirm "
                    "the previous entry."
                )

        # Record an expense
        elif "spent" in text or "expense" in text:
            match = re.search(
                r"(?:€\s*)?(\d+(?:[.,]\d{1,2})?)",
                text
            )

            if match:
                amount = float(
                    match.group(1).replace(",", ".")
                )

                category = "Other"

                if any(w in text for w in ["food", "grocer", "lunch"]):
                    category = "Food"
                elif any(w in text for w in ["bus", "train", "transport"]):
                    category = "Transport"
                elif "shopping" in text:
                    category = "Shopping"
                elif any(w in text for w in ["rent", "bill"]):
                    category = "Bills"

                st.session_state.pending_action = {
                    "tool": "log_expense",
                    "arguments": {
                        "amount": amount,
                        "category": category,
                        "note": "Recorded via FinMood chat"
                    }
                }

                reply = (
                    f"Would you like me to save a "
                    f"€{amount:.2f} expense under "
                    f"{category}? Reply yes or no."
                )

            else:
                reply = (
                    "Tell me an amount, for example: "
                    "'I spent €25 on groceries.'"
                )

        # Record an optional mood
        elif any(word in text for word in [
            "feeling", "feel", "mood"
        ]):
            moods = {
                "happy": "Happy",
                "calm": "Calm",
                "neutral": "Neutral",
                "stressed": "Stressed",
                "sad": "Sad",
                "anxious": "Anxious",
            }

            detected = next(
                (
                    value
                    for key, value in moods.items()
                    if key in text
                ),
                None
            )

            if detected:
                st.session_state.pending_action = {
                    "tool": "record_mood",
                    "arguments": {
                        "mood": detected,
                        "note": ""
                    }
                }

                reply = (
                    f"Would you like to record a "
                    f"{detected.lower()} mood check-in? "
                    "Reply yes or no."
                )
            else:
                reply = (
                    "You can optionally record how "
                    "you're feeling, for example: "
                    "'I'm feeling calm.'"
                )

        # Run a spending stress test
        elif "what if" in text or "stress test" in text:

            match = re.search(
                r"(\d+(?:\.\d+)?)\s*%",
                text
            )

            increase = (
                float(match.group(1))
                if match else 20.0
            )

            result = asyncio.run(
                call_tool(
                    "simulate_financial_stress",
                    {
                        "balance": balance,
                        "monthly_income": income,
                        "reserve": reserve,
                        "spending_increase_percent": increase,
                        "horizon": 30,
                    }
                )
            )

            reply = (
                f"With spending increased by {increase:.0f}%:\n\n"
                f"- Baseline ending balance: "
                f"€{result['baseline_ending_balance']:,.2f}\n"
                f"- Stressed ending balance: "
                f"€{result['stressed_ending_balance']:,.2f}\n"
                f"- Baseline reserve-breach probability: "
                f"{result['baseline_breach_probability']:.1%}\n"
                f"- Stressed reserve-breach probability: "
                f"{result['stressed_breach_probability']:.1%}"
            )

        # Financial forecast
        elif any(word in text for word in [
            "risk", "forecast", "balance", "money"
        ]):

            result = asyncio.run(
                call_tool(
                    "forecast_cashflow",
                    {
                        "balance": balance,
                        "monthly_income": income,
                        "reserve": reserve,
                        "horizon": 30,
                    }
                )
            )

            reply = (
                f"I ran {result['simulations']:,} "
                f"Monte Carlo simulations.\n\n"
                f"- Expected ending balance: "
                f"€{result['expected_ending_balance']:,.2f}\n"
                f"- Probability of falling below reserve: "
                f"{result['probability_reserve_breach']:.1%}\n"
                f"- Liquidity-at-Risk (95%): "
                f"€{result['liquidity_at_risk_95']:,.2f}\n"
                f"- Expected Shortfall (95%): "
                f"€{result['expected_shortfall_95']:,.2f}\n\n"
                "These are illustrative estimates."
            )

        else:
            reply = (
                "I can help you record an expense, "
                "save an optional mood check-in, "
                "forecast cash flow, or run a stress test."
            )

    except Exception as error:
        reply = f"Something went wrong: {error}"

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply,
    })

    with st.chat_message("assistant"):
        st.markdown(reply)