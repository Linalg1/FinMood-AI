import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():

    url = "http://127.0.0.1:8001/mcp"

    async with streamablehttp_client(url) as (
        read,
        write,
        _,
    ):

        async with ClientSession(read, write) as session:

            await session.initialize()

            print("\nConnected to FinMood MCP!")

            # Discover available tools

            tools = await session.list_tools()

            print("\nAvailable tools:")

            for tool in tools.tools:
                print("-", tool.name)

            # Run a financial risk calculation

            print("\nRunning Monte Carlo forecast...")

            result = await session.call_tool(
                "forecast_cashflow",
                arguments={
                    "balance": 1800,
                    "monthly_income": 2200,
                    "reserve": 200,
                    "horizon": 30,
                },
            )

            print("\nForecast result:")

            for content in result.content:
                if content.type == "text":
                    print(content.text)


if __name__ == "__main__":
    asyncio.run(main())