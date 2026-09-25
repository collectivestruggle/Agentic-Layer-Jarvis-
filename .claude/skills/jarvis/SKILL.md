---
name: jarvis
description: Operate through the OpenJarvis agentic layer. Use for repo work in Jarvis mode (file, git, shell, memory, knowledge-graph tools) when the mcp__openjarvis__* tools are missing from the session, or to talk to a deployed OpenJarvis server in the cloud (health, models, tools, ask its agent). Triggers on "jarvis", "openjarvis", "Jarvis mode", "use the agentic layer", "ask the cloud Jarvis".
---

# Jarvis

Two ways to reach OpenJarvis. Pick by what you need:

| Need | Mode |
|---|---|
| Run a Jarvis tool on this repo (read/write files, git, shell, memory, KG) | **Local MCP** |
| Talk to a Jarvis server someone deployed (Render, a VM, a tunnel) | **Cloud** |

In both, `$SKILL` is this skill's directory (`.claude/skills/jarvis`) and
`$REPO` is the repo root (the directory containing `pyproject.toml`).

## Local MCP

If `mcp__openjarvis__*` tools are already in the session, call them
directly; this mode is for when they are not (a session started outside the
repo, the server not yet approved, or a cloud session that did not load
`.mcp.json`). Say which case you are in.

The script is its own MCP client: it starts `python -m openjarvis.mcp` for
each call, so it needs nothing from the session config.

```bash
J() { uv run --quiet --project "$REPO" python "$REPO/$SKILL/scripts/jarvis_mcp.py" "$@"; }
J list                                  # tool names + one-line descriptions
J schema git_log                        # JSON input schema: check arg names first
J call git_status '{"repo_path": "."}'
J call git_log '{"repo_path": ".", "count": 5}'
J call file_read '{"path": "README.md"}'
echo '{"path": "notes.md", "content": "..."}' | J call file_write -
```

Rules:

- Run `J schema <tool>` before the first call to any tool; argument names are
  not guessable (for example `git_log` takes `count`, not `limit`). Unknown
  arguments are silently ignored, so a wrong name looks like success.
- Exit codes: `0` ok, `1` the tool itself reported an error (output is the
  error text), `2` bad arguments, unknown tool, or the server failed.
  Treat `1` and `2` as failures; don't paraphrase them as success.
- Empty output with exit `0` is a real result (for example `git_status` on
  a clean tree), not a failure.
- `file_write` and `apply_patch` change state and work over MCP; they run
  under the session's Bash permissions. Show the arguments you send.
- `git_commit` and `shell_exec` are **refused over MCP**: Jarvis marks them
  `requires_confirmation`, and its `ToolExecutor` rejects them when no
  confirmation callback is available ("requires confirmation but no
  confirmation callback is available", exit `1`). That is a Jarvis safety
  gate; don't work around it by editing Jarvis or the server. Use plain
  `git commit` / Bash instead and say that step bypassed Jarvis.
- Jarvis has no push tool. Push with plain `git push` and say so.
- First run in a fresh container installs dependencies via `uv` and can take
  minutes; later runs take a few seconds.

## Cloud

Talks to `jarvis serve` over HTTPS. Standard library only; no repo
environment needed.

Needs two environment variables, set by the user as environment secrets,
never written to files or echoed:

- `OPENJARVIS_URL`: base URL, e.g. `https://openjarvis-server.onrender.com`
- `OPENJARVIS_API_KEY`: the server's key (Render generates one; see
  `render.yaml` and `docs/deployment/render.md`)

```bash
C() { python3 "$REPO/$SKILL/scripts/jarvis_cloud.py" "$@"; }
C health                          # {"status": "ok"}
C models                          # models the server's engine serves
C tools                           # tools the server's agent can use
C ask "what's on my calendar?"    # one turn via /v1/chat/completions
C ask "..." --model gpt-4o-mini   # choose a model explicitly
```

- If either variable is unset, stop and tell the user what to set; don't
  hunt for keys elsewhere.
- Exit codes: `0` ok, `1` HTTP error from the server (`401` = wrong key,
  `503` = engine down), `2` config error or unreachable host. A free
  Render instance sleeps when idle; the first request can take ~1 min.
- The server exposes its *agent*, not raw tool execution. `ask` hands the
  prompt to whatever agent and model the server runs; the answer comes from
  that model, not from you. Say so when relaying it.
- The cloud host cannot see this container's files. For repo work use
  Local MCP.

## Reporting

State which mode ran, the exact command, and the exit code. If a mode is
unavailable (no `uv`, no network to the host, no URL/key), report it as
blocked and name what's missing instead of switching to built-in tools
without saying so.
