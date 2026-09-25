"""Agent 2 wrapper for operating through OpenJarvis.

This module deliberately lives outside OpenJarvis core.  It builds an isolated
Agent 2 JarvisSystem from normal OpenJarvis configuration, then exposes that
system's resolved tools as an MCP stdio server.

Run from the repository checkout:

    python -m agent2.wrapper

Optional:

    python -m agent2.wrapper --config /path/to/config.toml
    python -m agent2.wrapper --tools calculator,file_read,web_search

The wrapper writes protocol responses only to stdout. Diagnostics go to stderr.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Iterable

from openjarvis.mcp.protocol import INTERNAL_ERROR, INVALID_REQUEST, MCPRequest, MCPResponse
from openjarvis.mcp.server import MCPServer
from openjarvis.system.builder import SystemBuilder

AGENT2_ID = "agent-2"
DEFAULT_AGENT = "orchestrator"
DEFAULT_TOOLS = (
    "calculator",
    "file_read",
    "web_search",
    "memory_retrieve",
    "memory_search",
)

logger = logging.getLogger("openjarvis.agent2")


def _parse_tool_names(raw: str | None) -> list[str]:
    if not raw:
        return list(DEFAULT_TOOLS)
    return [name.strip() for name in raw.split(",") if name.strip()]


def build_agent2_system(
    *,
    config_path: str | None = None,
    tools: Iterable[str] = DEFAULT_TOOLS,
):
    """Build Agent 2's isolated JarvisSystem.

    Agent 2 gets its own runtime identity and an explicit tool allow-list.
    OpenJarvis core remains unchanged.
    """
    kwargs = {}
    if config_path:
        kwargs["config_path"] = Path(config_path).expanduser()

    builder = SystemBuilder(**kwargs)
    builder.agent(DEFAULT_AGENT)
    builder.tools(list(tools))
    builder.traces(True)
    builder.sessions(True)
    return builder.build()


def build_agent2_mcp(system) -> MCPServer:
    """Expose only Agent 2's resolved Jarvis tools through MCP."""
    return MCPServer(
        tools=list(system.tools),
        bus=system.bus,
        capability_policy=system.capability_policy,
        rate_limiter=system.rate_limiter,
        agent_id=AGENT2_ID,
    )


def serve_stdio(server: MCPServer) -> None:
    """Serve Jarvis MCP requests on stdin/stdout until the pipe closes."""
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            response = MCPResponse.error_response(
                0,
                INVALID_REQUEST,
                f"Invalid JSON: {exc.msg}",
            )
            print(response.to_json(), flush=True)
            continue

        # MCP notifications intentionally have no response.
        is_notification = isinstance(payload, dict) and "id" not in payload

        try:
            request = MCPRequest.from_json(line)
            response = server.handle(request)
            if not is_notification:
                print(response.to_json(), flush=True)
        except Exception as exc:
            logger.exception("Agent 2 MCP request failed")
            if not is_notification:
                request_id = payload.get("id", 0) if isinstance(payload, dict) else 0
                response = MCPResponse.error_response(
                    request_id,
                    INTERNAL_ERROR,
                    str(exc),
                )
                print(response.to_json(), flush=True)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Agent 2's OpenJarvis MCP wrapper.",
    )
    parser.add_argument(
        "--config",
        default=os.environ.get("AGENT2_JARVIS_CONFIG"),
        help="Optional OpenJarvis config.toml path.",
    )
    parser.add_argument(
        "--tools",
        default=os.environ.get("AGENT2_TOOLS"),
        help=(
            "Comma-separated Jarvis tool allow-list. "
            "Defaults to a conservative read-oriented starter set."
        ),
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    logging.basicConfig(
        level=os.environ.get("AGENT2_LOG_LEVEL", "INFO").upper(),
        stream=sys.stderr,
    )

    tool_names = _parse_tool_names(args.tools)
    logger.info("Starting %s with tools: %s", AGENT2_ID, ", ".join(tool_names))

    system = build_agent2_system(config_path=args.config, tools=tool_names)
    try:
        server = build_agent2_mcp(system)
        serve_stdio(server)
    finally:
        system.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
