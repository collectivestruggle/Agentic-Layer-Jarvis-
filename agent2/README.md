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
