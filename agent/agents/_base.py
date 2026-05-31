"""BaseAgent — Template Method pattern for all agent types.

Subclasses declare AGENT_NAME and SKILLS; BaseAgent handles:
  - system prompt assembly (base prompt file + skill sections)
  - allowed tools union
  - Langfuse tracing
  - Claude Agent SDK query loop + message streaming
"""

import asyncio
import os
from abc import ABC
from contextlib import contextmanager
from pathlib import Path
from typing import ClassVar

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

from ..skills._base import Skill

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
WORKSPACE = Path(os.environ.get("WORKSPACE", os.path.expanduser("~/workspace")))


class BaseAgent(ABC):  # noqa: B024
    AGENT_NAME: str = ""
    SKILLS: ClassVar[list[Skill]] = []

    # ------------------------------------------------------------------
    # Prompt + tool assembly
    # ------------------------------------------------------------------

    @classmethod
    def _base_prompt(cls) -> str:
        path = _PROMPTS_DIR / f"{cls.AGENT_NAME}.md"
        return path.read_text()

    @classmethod
    def system_prompt(cls) -> str:
        parts = [cls._base_prompt()]
        for skill in cls.SKILLS:
            parts.append(skill.prompt_section)
        return "\n\n".join(parts)

    @classmethod
    def allowed_tools(cls) -> list[str]:
        seen: set[str] = set()
        tools: list[str] = []
        for skill in cls.SKILLS:
            for t in skill.tools:
                if t not in seen:
                    seen.add(t)
                    tools.append(t)
        return tools

    # ------------------------------------------------------------------
    # Langfuse helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_langfuse():
        try:
            from langfuse import Langfuse

            if os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"):
                return Langfuse()
        except ImportError:
            pass
        return None

    @staticmethod
    @contextmanager
    def _nullctx():
        yield

    # ------------------------------------------------------------------
    # Template: run
    # ------------------------------------------------------------------

    @classmethod
    async def run(
        cls,
        prompt: str,
        verbose: bool = False,
        model: str | None = None,
        timeout: float | None = 600.0,
        dry_run: bool = False,
        **trace_meta,
    ) -> str:
        if dry_run:
            sys_p = cls.system_prompt()
            print(f"[dry-run] system_prompt:\n{sys_p}\n\n[dry-run] user prompt:\n{prompt}")  # noqa: T201
            return ""

        options = ClaudeAgentOptions(
            system_prompt=cls.system_prompt(),
            allowed_tools=cls.allowed_tools(),
            permission_mode="acceptEdits",
            cwd=str(WORKSPACE),
            model=model,
        )

        lf = cls._make_langfuse()
        result_text = ""
        session_id = None

        trace_ctx = (
            lf.start_as_current_observation(
                name=cls.AGENT_NAME,
                as_type="agent",
                input={"prompt": prompt[:200], **trace_meta},
                metadata={"workspace": str(WORKSPACE)},
            )
            if lf
            else None
        )

        try:
            with trace_ctx or cls._nullctx():
                tool_obs: dict[str, object] = {}

                async def _run_query():
                    nonlocal result_text, session_id

                    async for message in query(prompt=prompt, options=options):
                        if isinstance(message, SystemMessage) and message.subtype == "init":
                            session_id = message.data.get("session_id")
                            if lf:
                                lf.update_current_span(metadata={"session_id": session_id})
                            if verbose:
                                print(f"[session] {session_id}")  # noqa: T201

                        elif isinstance(message, AssistantMessage):
                            for block in message.content:
                                if isinstance(block, TextBlock):
                                    if verbose:
                                        print(block.text, end="", flush=True)  # noqa: T201
                                elif isinstance(block, ToolUseBlock):
                                    if verbose:
                                        print(  # noqa: T201
                                            f"\n[tool] {block.name}({_summarise(block.input)})"
                                        )
                                    if lf:
                                        obs = lf.start_observation(
                                            name=f"tool:{block.name}",
                                            as_type="tool",
                                            input=block.input,
                                        )
                                        tool_obs[block.id] = obs

                        elif isinstance(message, ResultMessage):
                            result_text = message.result or ""
                            status = "error" if message.subtype == "error" else "success"
                            if message.subtype == "error" and verbose:
                                print(f"[error] {result_text}", flush=True)  # noqa: T201
                            if verbose:
                                usage = getattr(message, "usage", None) or {}
                                inp = usage.get("input_tokens", "?")
                                out = usage.get("output_tokens", "?")
                                print(f"\n[tokens] input={inp} output={out}")  # noqa: T201
                            if lf:
                                for obs in tool_obs.values():
                                    obs.update(output={"status": "completed"}).end()
                                tool_obs.clear()
                                usage = getattr(message, "usage", None) or {}
                                lf.update_current_span(
                                    input={"prompt": prompt[:200], **trace_meta},
                                    output={"result": result_text[:500], "status": status},
                                    metadata={
                                        "session_id": session_id,
                                        "status": status,
                                        "input_tokens": usage.get("input_tokens"),
                                        "output_tokens": usage.get("output_tokens"),
                                    },
                                )

                max_attempts = 3
                for attempt in range(1, max_attempts + 1):
                    try:
                        await asyncio.wait_for(_run_query(), timeout=timeout)
                        break
                    except TimeoutError:
                        if lf:
                            lf.update_current_span(
                                metadata={"error": "timeout", "status": "timeout"}
                            )
                        raise
                    except Exception as exc:
                        if attempt == max_attempts:
                            if lf:
                                lf.update_current_span(
                                    metadata={"error": str(exc), "status": "exception"}
                                )
                            raise
                        wait = 2**attempt
                        if verbose:
                            print(f"[retry {attempt}/{max_attempts - 1}] {exc} — retry in {wait}s")  # noqa: T201
                        await asyncio.sleep(wait)

        finally:
            if lf:
                lf.flush()

        return result_text


def _summarise(d: dict) -> str:
    parts = []
    for k, v in list(d.items())[:3]:
        v_str = str(v)[:60].replace("\n", " ")
        parts.append(f"{k}={v_str!r}")
    return ", ".join(parts)
