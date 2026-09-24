"""Tests for the ``python -m openjarvis.mcp`` stdio entry point."""

from __future__ import annotations

import io
import json
import subprocess
import sys

import pytest

from openjarvis.mcp.__main__ import build_server, handle_line, serve
from openjarvis.mcp.protocol import INVALID_REQUEST, PARSE_ERROR
from openjarvis.mcp.server import MCPServer
from openjarvis.tools.calculator import CalculatorTool
from openjarvis.tools.think import ThinkTool


@pytest.fixture
def server() -> MCPServer:
    return MCPServer([CalculatorTool(), ThinkTool()])


def _frame(method: str, id: int | None = 1, **params) -> str:
    msg = {"jsonrpc": "2.0", "method": method, "params": params}
    if id is not None:
        msg["id"] = id
    return json.dumps(msg)


def test_initialize_and_list(server):
    init = json.loads(handle_line(server, _frame("initialize")))
    assert init["result"]["serverInfo"]["name"] == "openjarvis"

    listed = json.loads(handle_line(server, _frame("tools/list", id=2)))
    assert {t["name"] for t in listed["result"]["tools"]} == {"calculator", "think"}


def test_tools_call(server):
    resp = json.loads(
        handle_line(
            server,
            _frame("tools/call", name="calculator", arguments={"expression": "6*7"}),
        )
    )
    assert resp["result"]["isError"] is False
    assert "42" in resp["result"]["content"][0]["text"]


def test_notification_gets_no_response(server):
    assert handle_line(server, _frame("notifications/initialized", id=None)) is None


def test_ping(server):
    assert json.loads(handle_line(server, _frame("ping", id=9))) == {
        "jsonrpc": "2.0",
        "id": 9,
        "result": {},
    }


def test_parse_error(server):
    resp = json.loads(handle_line(server, "{not json"))
    assert resp["error"]["code"] == PARSE_ERROR


def test_invalid_request(server):
    resp = json.loads(handle_line(server, json.dumps({"id": 3})))
    assert resp["error"]["code"] == INVALID_REQUEST
    assert resp["id"] == 3


def test_serve_loop_skips_blank_lines(server):
    stdin = io.StringIO(
        "\n".join(
            [
                _frame("initialize", id=1),
                "",
                _frame("notifications/initialized", id=None),
                _frame("tools/list", id=2),
            ]
        )
        + "\n"
    )
    stdout = io.StringIO()
    serve(server, stdin, stdout)
    ids = [json.loads(line)["id"] for line in stdout.getvalue().splitlines()]
    assert ids == [1, 2]


def test_build_server_allowlist():
    srv = build_server(["calculator"])
    assert [t.spec.name for t in srv.get_tools()] == ["calculator"]


def test_build_server_unknown_tool():
    with pytest.raises(SystemExit):
        build_server(["no_such_tool"])


def test_subprocess_stdout_is_protocol_only():
    """Every stdout line from a real subprocess must be a JSON-RPC frame."""
    frames = "\n".join(
        [
            _frame("initialize", id=1),
            _frame("notifications/initialized", id=None),
            _frame("tools/list", id=2),
        ]
    )
    proc = subprocess.run(
        [sys.executable, "-m", "openjarvis.mcp", "--tools", "calculator,think"],
        input=frames + "\n",
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    lines = proc.stdout.splitlines()
    assert [json.loads(line)["id"] for line in lines] == [1, 2]
