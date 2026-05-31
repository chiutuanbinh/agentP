"""Agent builder — creates new agents using Claude Agent SDK and Langfuse docs."""

from typing import ClassVar

from ..skills import CODE_TOOLS, LANGFUSE_SKILL
from ..skills.agent_builder_docs import AGENT_BUILDER_DOCS
from ._base import WORKSPACE, BaseAgent


class AgentBuilderAgent(BaseAgent):
    AGENT_NAME = "agent_builder"
    SKILLS: ClassVar[list] = [AGENT_BUILDER_DOCS, CODE_TOOLS, LANGFUSE_SKILL]

    @classmethod
    def _base_prompt(cls) -> str:
        raw = super()._base_prompt()
        return raw.replace("{WORKSPACE}", str(WORKSPACE))


async def run(
    task: str,
    verbose: bool = False,
    model: str | None = None,
    dry_run: bool = False,
    timeout: float | None = 600.0,
) -> str:
    prompt = f"Task: {task}. Follow the agent builder workflow in your instructions exactly."
    return await AgentBuilderAgent.run(
        prompt, verbose=verbose, model=model, dry_run=dry_run, timeout=timeout, task=task[:100]
    )
