"""Call OpenJarvis tools through its MCP stdio server, from any shell.

Works whether or not the host session has loaded the ``openjarvis`` MCP
server: this script is its own MCP client and spawns ``python -m
openjarvis.mcp`` for each invocation.

Run it with the repo's environment::

    uv run --project "$REPO" python "$SKILL/scripts/jarvis_mcp.py" list
    uv run --project "$REPO" python "$SKILL/scripts/jarvis_mcp.py" \
        call git_status '{"repo_path": "."}'

Exit status: 0 on success, 1 if the tool reported an error, 2 on usage or
protocol errors.
"""

from __future__ import annotations

import argparse
import json
import sys

from openjarvis.mcp import MCPClient, StdioTransport
from openjarvis.mcp.protocol import MCPError


def _client(tools: str | None) -> MCPClient:
    cmd = [sys.executable, "-m", "openjarvis.mcp"]
    if tools:
        cmd += ["--tools", tools]
    client = MCPClient(StdioTransport(cmd, response_timeout=300.0))
    client.initialize()
    return client


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jarvis_mcp")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="List available Jarvis tools.")
    schema = sub.add_parser("schema", help="Print a tool's JSON input schema.")
    schema.add_argument("tool")
    call = sub.add_parser("call", help="Call one Jarvis tool.")
    call.add_argument("tool")
    call.add_argument(
        "arguments",
        nargs="?",
        default="{}",
        help="JSON object of tool arguments, or '-' to read it from stdin.",
    )
    args = parser.parse_args(argv)

    if args.cmd == "list":
        with _client(None) as client:
            for spec in client.list_tools():
                first = (spec.description or "").strip().splitlines()
                print(f"{spec.name}\t{first[0] if first else ''}")
        return 0

    if args.cmd == "schema":
        with _client(None) as client:
            for spec in client.list_tools():
                if spec.name == args.tool:
                    print(json.dumps(spec.parameters, indent=2))
                    return 0
        print(f"unknown tool: {args.tool}", file=sys.stderr)
        return 2

    raw = sys.stdin.read() if args.arguments == "-" else args.arguments
    try:
        arguments = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"arguments are not valid JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(arguments, dict):
        print("arguments must be a JSON object", file=sys.stderr)
        return 2

    # Restrict the spawned server to the one tool being called.
    try:
        with _client(args.tool) as client:
            result = client.call_tool(args.tool, arguments)
    except MCPError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:  # includes the server exiting on an unknown tool
        print(f"Jarvis MCP call failed: {exc}", file=sys.stderr)
        return 2

    for item in result.get("content", []):
        if item.get("type") == "text":
            print(item.get("text", ""))
        else:
            print(json.dumps(item))
    return 1 if result.get("isError") else 0


if __name__ == "__main__":
    sys.exit(main())
