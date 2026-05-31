"""Data engineer agent — ticket-to-PR workflow for data pipelines."""

from typing import ClassVar

from ..skills import AZURE_DATA, CODE_TOOLS, CONFLUENCE, DATABRICKS, GITHUB, JIRA, POSTGRES, SLACK
from ._base import WORKSPACE, BaseAgent


class DataEngineerAgent(BaseAgent):
    AGENT_NAME = "data_engineer"
    SKILLS: ClassVar[list] = [JIRA, GITHUB, CONFLUENCE, CODE_TOOLS, POSTGRES, AZURE_DATA, DATABRICKS, SLACK]

    @classmethod
    def _base_prompt(cls) -> str:
        raw = super()._base_prompt()
        return raw.replace("{WORKSPACE}", str(WORKSPACE))


async def run(
    ticket_key: str,
    repo_path: str | None = None,
    verbose: bool = False,
    model: str | None = None,
    dry_run: bool = False,
    timeout: float | None = 600.0,
) -> str:
    prompt = f"Implement Jira ticket {ticket_key}."
    if repo_path:
        prompt += f" The repository is already checked out at {repo_path}."
    prompt += " Follow the data engineer workflow in your instructions exactly."
    return await DataEngineerAgent.run(
        prompt, verbose=verbose, model=model, dry_run=dry_run, timeout=timeout, ticket=ticket_key
    )
