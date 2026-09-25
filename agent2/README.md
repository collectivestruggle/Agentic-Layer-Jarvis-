# Agent 2 Jarvis Wrapper

This directory is Agent 2's isolated doorway into the OpenJarvis runtime.

It is intentionally kept outside `src/openjarvis` so Agent 2 can evolve its
integration without changing OpenJarvis core or interfering with Agent 1.

## What it does

`agent2.wrapper`:

1. builds a normal `JarvisSystem` using OpenJarvis's existing `SystemBuilder`;
2. identifies the runtime as `agent-2`;
3. applies an explicit Jarvis tool allow-list;
4. reuses the system's security policy and rate limiter;
5. exposes the resolved Jarvis tools through OpenJarvis's existing MCP server;
6. speaks MCP JSON-RPC over stdin/stdout so an external OpenAI agent runtime can
   operate through those tools.

The initial default tools are deliberately conservative:

- `calculator`
- `file_read`
- `web_search`
- `memory_retrieve`
- `memory_search`

Higher-impact tools such as file writing, shell execution, patching, messaging,
and scheduling should be added explicitly after the bridge is verified.

## Run

From a checkout of this branch with OpenJarvis installed:

```bash
python -m agent2.wrapper
```

Use a particular OpenJarvis config:

```bash
python -m agent2.wrapper --config ~/.openjarvis/config.toml
```

Choose Agent 2's Jarvis tools explicitly:

```bash
python -m agent2.wrapper --tools calculator,file_read,web_search
```

The same settings may be supplied with:

- `AGENT2_JARVIS_CONFIG`
- `AGENT2_TOOLS`
- `AGENT2_LOG_LEVEL`

## Boundary

This wrapper does not modify `main`. All Agent 2 integration work belongs on
`agent-2/jarvis-openai-agent` until Geoffrey explicitly chooses otherwise.

This first wrapper creates the Jarvis side of the bridge. The next integration
step is attaching an OpenAI agent runtime to this MCP process and proving a
round-trip tool call.

## OpenAI agent bridge

The next layer is implemented in `agent2/openai_bridge.py`.

It uses OpenAI's official Agents SDK `MCPServerStdio` transport to launch this
branch's Jarvis wrapper as a subprocess. The OpenAI agent then receives the
Jarvis tools through MCP.

Check that the OpenAI SDK can discover the Jarvis tool surface without making a
model call:

```bash
uv run --with openai-agents pytest tests/agent2/test_openai_bridge.py -q
```

Run a live OpenAI agent through Jarvis:

```bash
export OPENAI_API_KEY=...
uv run --with openai-agents python -m agent2.openai_bridge "Calculate 6 times 7."
```

The live run requires an OpenAI API credential in the runtime. The credential
is read from the environment and is never stored in this repository.
