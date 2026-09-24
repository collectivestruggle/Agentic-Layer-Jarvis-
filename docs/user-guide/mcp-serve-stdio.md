# Serving OpenJarvis Tools over MCP (stdio)

OpenJarvis can act as an MCP **server**, so an external agent host such as
Claude Code or Claude Desktop drives the OpenJarvis tool layer (file I/O,
git, shell, memory, knowledge graph) directly.

```bash
python -m openjarvis.mcp                                 # every discovered tool
python -m openjarvis.mcp --tools file_read,git_status   # explicit allowlist
```

Frames are newline-delimited JSON-RPC 2.0 on stdin/stdout; logs go to stderr.

## Claude Code

The repository ships a project-scoped `.mcp.json` that registers the server
as `openjarvis` with a repo-operating allowlist. Start `claude` in the repo
root and approve the server when prompted (or check with `claude mcp list`).
Tools then appear as `mcp__openjarvis__<tool>`, and each call still goes
through Claude Code's permission prompts.

Edit the `--tools` list in `.mcp.json` to widen or narrow what is exposed.
Omitting `--tools` exposes everything `MCPServer` auto-discovers, including
`http_request`, `channel_send` and `code_interpreter`.

## The other direction

To run OpenJarvis's own agents *on* Claude instead, use the cloud engine:
`ANTHROPIC_API_KEY=... ./scripts/launch-claude.sh`.
