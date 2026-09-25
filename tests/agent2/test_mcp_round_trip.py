from __future__ import annotations

from openjarvis.mcp.protocol import MCPRequest
from openjarvis.mcp.server import MCPServer
from openjarvis.tools.calculator import CalculatorTool


def test_agent2_mcp_calculator_round_trip() -> None:
    server = MCPServer(tools=[CalculatorTool()], agent_id="agent-2")

    init = server.handle(MCPRequest(method="initialize", id=1))
    assert init.error is None
    assert init.result["serverInfo"]["name"] == "openjarvis"

    listed = server.handle(MCPRequest(method="tools/list", id=2))
    assert listed.error is None
    names = [tool["name"] for tool in listed.result["tools"]]
    assert names == ["calculator"]

    called = server.handle(
        MCPRequest(
            method="tools/call",
            params={"name": "calculator", "arguments": {"expression": "6*7"}},
            id=3,
        )
    )
    assert called.error is None
    assert called.result["isError"] is False
    assert called.result["content"][0]["text"] == "42.0"
