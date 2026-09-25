# Jarvis mode

This branch (`claude/zealous-mccarthy-ibeds8`) runs Claude Code *through* the
OpenJarvis agentic layer. `.mcp.json` starts `python -m openjarvis.mcp`, and
`.claude/settings.json` enables it, so a session started on this branch has
the Jarvis tools as `mcp__openjarvis__*`.

## Operating rules

- Do repo work through the Jarvis layer when a Jarvis tool covers it:
  - read files: `mcp__openjarvis__file_read`
  - write/edit: `mcp__openjarvis__file_write`, `mcp__openjarvis__apply_patch`
  - git: `mcp__openjarvis__git_status`, `git_diff`, `git_log`, `git_commit`
  - commands: `mcp__openjarvis__shell_exec`
  - notes that should persist across sessions: `mcp__openjarvis__memory_store`
    / `memory_search`, `kg_add_entity` / `kg_query`
- Fall back to Claude Code's built-in tools only when no Jarvis tool fits,
  and say so. Known gaps: pushing (no Jarvis tool), and `git_commit` /
  `shell_exec`, which Jarvis refuses over MCP because they need an
  interactive confirmation callback the MCP server does not have.
- If the `mcp__openjarvis__*` tools are missing, report it and use the
  `jarvis` skill (`.claude/skills/jarvis`), which reaches the same tools
  through its own MCP client; don't silently carry on with built-in tools.
  To load the native tools, check `claude mcp list` or reconnect via `/mcp`.
- To talk to a deployed OpenJarvis server, use the `jarvis` skill's cloud
  mode (`OPENJARVIS_URL` + `OPENJARVIS_API_KEY`).
- Read-only Jarvis tools are pre-allowed in `.claude/settings.json`; writes
  still ask for permission.
- Work on this branch; do not open PRs to `main` unless asked.
