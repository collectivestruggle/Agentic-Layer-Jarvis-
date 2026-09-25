"""OpenAI Agents SDK bridge into the Agent 2 OpenJarvis wrapper."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from agents.model_settings import ModelSettings

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.6-sol")
DEFAULT_TOOLS = os.environ.get("AGENT2_TOOLS", "calculator")


def make_mcp_server(tool_names: str = DEFAULT_TOOLS) -> MCPServerStdio:
    """Launch this branch's Jarvis wrapper as a local MCP subprocess."""
    return MCPServerStdio(
        name="OpenJarvis",
        params={
            "command": sys.executable,
            "args": [
                "-m",
                "agent2.wrapper",
                "--tools",
                tool_names,
            ],
        },
        cache_tools_list=True,
        require_approval="never",
    )


async def run_openai_agent(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    tool_names: str = DEFAULT_TOOLS,
) -> str:
    """Run an OpenAI agent whose tools come from the Jarvis MCP wrapper."""
    async with make_mcp_server(tool_names) as server:
        agent = Agent(
            name="OpenAI Agent",
            instructions=(
                "Use the OpenJarvis MCP tools when they are needed. "
                "For arithmetic, use the calculator tool rather than doing the math yourself."
            ),
            model=model,
            mcp_servers=[server],
            model_settings=ModelSettings(tool_choice="required"),
        )
        result = await Runner.run(agent, prompt)
        return result.final_output


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run an OpenAI agent through the Agent 2 Jarvis MCP wrapper.",
    )
    parser.add_argument("prompt", nargs="+", help="Prompt for the OpenAI agent.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--tools", default=DEFAULT_TOOLS)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit(
            "OPENAI_API_KEY is required for a live OpenAI agent run."
        )

    output = asyncio.run(
        run_openai_agent(
            " ".join(args.prompt),
            model=args.model,
            tool_names=args.tools,
        )
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
