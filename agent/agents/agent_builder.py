"""Agent builder — creates new agents using Claude Agent SDK and Langfuse docs."""

from typing import ClassVar

from ..skills import CODE_TOOLS
from ..skills.agent_builder_docs import AGENT_BUILDER_DOCS
from ._base import WORKSPACE, BaseAgent


class AgentBuilderAgent(BaseAgent):
    AGENT_NAME = "agent_builder"
    SKILLS: ClassVar[list] = [AGENT_BUILDER_DOCS, CODE_TOOLS]

    @classmethod
    def _base_prompt(cls) -> str:
        raw = super()._base_prompt()
        return raw.replace("{WORKSPACE}", str(WORKSPACE))


async def run(task: str, verbose: bool = False) -> str:
    prompt = f"Task: {task}. Follow the agent builder workflow in your instructions exactly."
    return await AgentBuilderAgent.run(prompt, verbose=verbose, task=task[:100])
