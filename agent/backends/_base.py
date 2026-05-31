"""LLMBackend protocol — strategy interface for agent execution backends."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class BackendResult:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    session_id: str | None = None
    backend: str = ""
    tool_calls: list[str] = field(default_factory=list)


class LLMBackend(ABC):
    """Strategy interface: one implementation per LLM runtime."""

    name: str = ""

    @abstractmethod
    async def run(
        self,
        prompt: str,
        system_prompt: str,
        allowed_tools: list[str],
        model: str | None,
        cwd: str,
        verbose: bool,
        timeout: float | None,
        langfuse: object | None,
        trace_meta: dict,
        mcp_servers: dict,
    ) -> BackendResult: ...
