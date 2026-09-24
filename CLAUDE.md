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
- Fall back to Claude Code's built-in tools only when no Jarvis tool fits
  (for example pushing, which Jarvis has no tool for), and say so.
- If the `mcp__openjarvis__*` tools are missing, report it; don't silently
  carry on without them. Check with `claude mcp list`, or reconnect via
  `/mcp`.
- Read-only Jarvis tools are pre-allowed in `.claude/settings.json`; writes,
  commits and shell still ask for permission.
- Work on this branch; do not open PRs to `main` unless asked.
