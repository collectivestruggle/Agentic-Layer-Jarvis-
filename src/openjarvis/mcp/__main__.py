"""Serve OpenJarvis tools over MCP stdio.

Lets an external MCP host (Claude Code, Claude Desktop, any MCP client) drive
the OpenJarvis tool layer::

    python -m openjarvis.mcp                       # every discovered tool
    python -m openjarvis.mcp --tools file_read,git_status,git_diff

Messages are newline-delimited JSON-RPC 2.0 on stdin/stdout.  Only protocol
messages are written to stdout; logs go to stderr.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
import sys
from typing import IO, List, Optional

from openjarvis.mcp.protocol import (
    INVALID_PARAMS,
    INVALID_REQUEST,
    PARSE_ERROR,
    MCPRequest,
    MCPResponse,
)
from openjarvis.mcp.server import MCPServer

logger = logging.getLogger(__name__)


def build_server(tool_names: Optional[List[str]] = None) -> MCPServer:
    """Create an ``MCPServer``, optionally restricted to *tool_names*."""
    # Tool discovery may print; keep stdout reserved for protocol frames.
    with contextlib.redirect_stdout(sys.stderr):
        server = MCPServer()
    if tool_names is None:
        return server
    available = {t.spec.name: t for t in server.get_tools()}
    missing = [n for n in tool_names if n not in available]
    if missing:
        raise SystemExit(f"unknown tool(s): {', '.join(missing)}")
    return MCPServer([available[n] for n in tool_names])


def handle_line(server: MCPServer, line: str) -> Optional[str]:
    """Process one stdin frame; return the response frame, or ``None``."""
    try:
        parsed = json.loads(line)
    except json.JSONDecodeError as exc:
        return MCPResponse.error_response(None, PARSE_ERROR, str(exc)).to_json()
    if not isinstance(parsed, dict) or "method" not in parsed:
        req_id = parsed.get("id") if isinstance(parsed, dict) else None
        return MCPResponse.error_response(
            req_id, INVALID_REQUEST, "Invalid request"
        ).to_json()

    # JSON-RPC notifications (no id) never get a response.
    if "id" not in parsed:
        return None

    params = parsed.get("params") or {}
    if not isinstance(params, dict):
        return MCPResponse.error_response(
            parsed["id"], INVALID_PARAMS, "params must be an object"
        ).to_json()

    request = MCPRequest(method=parsed["method"], params=params, id=parsed["id"])
    if request.method == "ping":
        return MCPResponse(result={}, id=request.id).to_json()
    with contextlib.redirect_stdout(sys.stderr):
        response = server.handle(request)
    return response.to_json()


def serve(server: MCPServer, stdin: IO[str], stdout: IO[str]) -> None:
    """Read frames from *stdin* until EOF, writing responses to *stdout*."""
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        out = handle_line(server, line)
        if out is not None:
            stdout.write(out + "\n")
            stdout.flush()


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m openjarvis.mcp",
        description="Serve OpenJarvis tools over MCP stdio.",
    )
    parser.add_argument(
        "--tools",
        help="Comma-separated allowlist of tool names (default: all discovered).",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

    tool_names = (
        [n.strip() for n in args.tools.split(",") if n.strip()] if args.tools else None
    )
    server = build_server(tool_names)
    serve(server, sys.stdin, sys.stdout)


if __name__ == "__main__":
    main()
