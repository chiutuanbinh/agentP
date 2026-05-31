"""SWE agent — ticket-to-PR workflow."""

from typing import ClassVar

from ..skills import CODE_TOOLS, CONFLUENCE, GITHUB, JIRA, SLACK
from ._base import WORKSPACE, BaseAgent


class SWEAgent(BaseAgent):
    AGENT_NAME = "swe"
    SKILLS: ClassVar[list] = [JIRA, GITHUB, CONFLUENCE, CODE_TOOLS, SLACK]

    @classmethod
    def _base_prompt(cls) -> str:
        raw = super()._base_prompt()
        # Inject runtime WORKSPACE path into prompt
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
    prompt += " Follow the SWE workflow in your instructions exactly."
    return await SWEAgent.run(
        prompt, verbose=verbose, model=model, dry_run=dry_run, timeout=timeout, ticket=ticket_key
    )
