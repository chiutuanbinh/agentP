"""Tests for Skill dataclass and BaseAgent template methods."""

import asyncio
import sys
from io import StringIO
from typing import ClassVar
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Patch heavy imports before agent modules are imported
# ---------------------------------------------------------------------------
_sdk_mock = MagicMock()
sys.modules.setdefault("claude_agent_sdk", _sdk_mock)
sys.modules.setdefault("langfuse", MagicMock())

from agent.agents._base import BaseAgent  # noqa: E402
from agent.skills._base import Skill  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SKILL_A = Skill(name="alpha", tools=("Read", "Write"), prompt_section="## Alpha\nDo alpha.")
SKILL_B = Skill(name="beta", tools=("Write", "Bash"), prompt_section="## Beta\nDo beta.")


class _ConcreteAgent(BaseAgent):
    AGENT_NAME = "test_agent"
    SKILLS: ClassVar[list[Skill]] = [SKILL_A, SKILL_B]


# ---------------------------------------------------------------------------
# 1. Skill dataclass
# ---------------------------------------------------------------------------


class TestSkill:
    def test_fields_stored(self):
        assert SKILL_A.name == "alpha"
        assert SKILL_A.tools == ("Read", "Write")
        assert SKILL_A.prompt_section == "## Alpha\nDo alpha."

    def test_frozen_raises_on_mutate(self):
        import dataclasses

        assert dataclasses.fields(Skill)  # is a dataclass
        try:
            SKILL_A.name = "mutated"  # type: ignore[misc]
            raise AssertionError("Expected FrozenInstanceError")
        except Exception as exc:
            assert "frozen" in type(exc).__name__.lower() or "cannot" in str(exc).lower()


# ---------------------------------------------------------------------------
# 2. BaseAgent.system_prompt()
# ---------------------------------------------------------------------------


class TestSystemPrompt:
    def test_includes_base_and_skill_sections(self):
        base = "You are a test agent."
        with patch.object(_ConcreteAgent, "_base_prompt", return_value=base):
            result = _ConcreteAgent.system_prompt()

        assert result.startswith(base)
        assert SKILL_A.prompt_section in result
        assert SKILL_B.prompt_section in result

    def test_sections_joined_with_double_newline(self):
        base = "BASE"
        with patch.object(_ConcreteAgent, "_base_prompt", return_value=base):
            result = _ConcreteAgent.system_prompt()

        expected = "\n\n".join([base, SKILL_A.prompt_section, SKILL_B.prompt_section])
        assert result == expected


# ---------------------------------------------------------------------------
# 3. BaseAgent.allowed_tools()
# ---------------------------------------------------------------------------


class TestAllowedTools:
    def test_deduplicates_preserves_order(self):
        # SKILL_A: Read, Write — SKILL_B: Write (dup), Bash
        tools = _ConcreteAgent.allowed_tools()
        assert tools == ["Read", "Write", "Bash"]

    def test_no_agent_no_tools(self):
        class _Empty(BaseAgent):
            AGENT_NAME = "empty"
            SKILLS: ClassVar[list[Skill]] = []

        assert _Empty.allowed_tools() == []

    def test_single_skill(self):
        class _One(BaseAgent):
            AGENT_NAME = "one"
            SKILLS: ClassVar[list[Skill]] = [SKILL_A]

        assert _One.allowed_tools() == ["Read", "Write"]


# ---------------------------------------------------------------------------
# 4. BaseAgent.run() with dry_run=True
# ---------------------------------------------------------------------------


class TestDryRun:
    def _run_dry(self, prompt="hello"):
        captured = StringIO()
        with patch("sys.stdout", captured):
            result = asyncio.run(_ConcreteAgent.run(prompt, dry_run=True))
        return result, captured.getvalue()

    def test_returns_empty_string(self):
        with patch.object(_ConcreteAgent, "_base_prompt", return_value="BASE"):
            result, _ = self._run_dry()
        assert result == ""

    def test_prints_something(self):
        with patch.object(_ConcreteAgent, "_base_prompt", return_value="BASE"):
            _, output = self._run_dry("test prompt")
        assert len(output) > 0
        assert "dry-run" in output.lower() or "dry_run" in output.lower() or "dry" in output

    def test_query_never_called(self):
        backend_mock = MagicMock()
        with (
            patch.object(_ConcreteAgent, "_base_prompt", return_value="BASE"),
            patch("agent.backends.claude.query", backend_mock),
        ):
            asyncio.run(_ConcreteAgent.run("anything", dry_run=True))
            backend_mock.assert_not_called()
