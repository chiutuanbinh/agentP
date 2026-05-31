"""Data analyst agent — ticket-to-insight workflow for business analysis."""

from typing import ClassVar

from ..skills import AZURE_DATA, CODE_TOOLS, CONFLUENCE, DATABRICKS, JIRA, POSTGRES, SLACK
from ._base import WORKSPACE, BaseAgent


class DataAnalystAgent(BaseAgent):
    AGENT_NAME = "data_analyst"
    SKILLS: ClassVar[list] = [JIRA, CONFLUENCE, CODE_TOOLS, POSTGRES, AZURE_DATA, DATABRICKS, SLACK]

    @classmethod
    def _base_prompt(cls) -> str:
        raw = super()._base_prompt()
        return raw.replace("{WORKSPACE}", str(WORKSPACE))


async def run(
    ticket_key: str,
    task: str | None = None,
    verbose: bool = False,
    model: str | None = None,
    dry_run: bool = False,
    timeout: float | None = 600.0,
) -> str:
    prompt = f"Ticket: {ticket_key}."
    if task:
        prompt += f" Task: {task}."
    prompt += " Follow the data analyst workflow in your instructions exactly."
    return await DataAnalystAgent.run(
        prompt, verbose=verbose, model=model, dry_run=dry_run, timeout=timeout, ticket=ticket_key
    )
