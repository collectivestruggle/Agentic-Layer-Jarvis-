from __future__ import annotations

import pytest

from agents import Agent
from agents.mcp import MCPServerStdio
from agents.run_context import RunContextWrapper

from agent2.openai_bridge import make_mcp_server


@pytest.mark.asyncio
async def test_openai_sdk_discovers_jarvis_calculator() -> None:
    server: MCPServerStdio = make_mcp_server("calculator")

    async with server:
        agent = Agent(
            name="Bridge Test",
            instructions="Use the available MCP tools.",
            mcp_servers=[server],
        )
        context = RunContextWrapper(context=None)
        tools = await agent.get_mcp_tools(context)

    names = [tool.name for tool in tools]
    assert names == ["calculator"]
