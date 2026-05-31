"""BaseAgent — Template Method pattern for all agent types.

Subclasses declare AGENT_NAME, SKILLS, and optionally BACKEND.
BaseAgent handles prompt assembly, Langfuse trace wrapping, and backend dispatch.
"""

import os
from abc import ABC
from contextlib import contextmanager
from pathlib import Path
from typing import ClassVar

from ..backends import ClaudeBackend, LLMBackend
from ..skills._base import Skill

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
WORKSPACE = Path(os.environ.get("WORKSPACE", os.path.expanduser("~/workspace")))


class BaseAgent(ABC):  # noqa: B024
    AGENT_NAME: str = ""
    SKILLS: ClassVar[list[Skill]] = []
    MCP_SERVERS: ClassVar[dict] = {}
    BACKEND: ClassVar[type[LLMBackend]] = ClaudeBackend

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
        backend: type[LLMBackend] | None = None,
        **trace_meta,
    ) -> str:
        if dry_run:
            sys_p = cls.system_prompt()
            print(f"[dry-run] system_prompt:\n{sys_p}\n\n[dry-run] user prompt:\n{prompt}")  # noqa: T201
            return ""

        backend_cls = backend or cls.BACKEND
        backend_instance = backend_cls()

        lf = cls._make_langfuse()
        trace_ctx = (
            lf.start_as_current_observation(
                name=cls.AGENT_NAME,
                as_type="agent",
                input={"prompt": prompt[:200], "backend": backend_instance.name, **trace_meta},
                metadata={"workspace": str(WORKSPACE), "backend": backend_instance.name},
            )
            if lf
            else None
        )

        try:
            with trace_ctx or cls._nullctx():
                result = await backend_instance.run(
                    prompt=prompt,
                    system_prompt=cls.system_prompt(),
                    allowed_tools=cls.allowed_tools(),
                    model=model,
                    cwd=str(WORKSPACE),
                    verbose=verbose,
                    timeout=timeout,
                    langfuse=lf,
                    trace_meta=trace_meta,
                    mcp_servers=cls.MCP_SERVERS,
                )
        finally:
            if lf:
                lf.flush()

        return result.text
