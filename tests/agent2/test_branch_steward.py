from __future__ import annotations

from pathlib import Path

from openjarvis.agents.manager import AgentManager


def test_branch_steward_template_is_discoverable_and_branch_bounded(tmp_path: Path) -> None:
    templates = AgentManager.list_templates()
    steward = next(t for t in templates if t.get("id") == "branch_steward")

    assert steward["agent_type"] == "monitor_operative"
    assert "git_status" in steward["tools"]
    assert "git_commit" in steward["tools"]
    assert "shell_exec" in steward["tools"]

    manager = AgentManager(str(tmp_path / "agents.db"))
    try:
        agent = manager.create_from_template(
            "branch_steward",
            "Agent 2 Branch Steward",
            overrides={"instruction": "Maintain the isolated integration branch."},
        )
    finally:
        manager.close()

    prompt = agent["config"]["system_prompt"]
    assert "agent-2/jarvis-openai-agent" in prompt
    assert "never modify, merge into, push to, reset, or rewrite main" in prompt.lower()
    assert "Maintain the isolated integration branch." in prompt
