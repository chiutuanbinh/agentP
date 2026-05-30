"""SWE agent — ticket-to-PR workflow."""

from ..skills import CODE_TOOLS, CONFLUENCE, GITHUB, JIRA
from ._base import BaseAgent, WORKSPACE


class SWEAgent(BaseAgent):
    AGENT_NAME = "swe"
    SKILLS = [JIRA, GITHUB, CONFLUENCE, CODE_TOOLS]

    @classmethod
    def _base_prompt(cls) -> str:
        raw = super()._base_prompt()
        # Inject runtime WORKSPACE path into prompt
        return raw.replace("{WORKSPACE}", str(WORKSPACE))


async def run(ticket_key: str, repo_path: str | None = None, verbose: bool = False) -> str:
    prompt = f"Implement Jira ticket {ticket_key}."
    if repo_path:
        prompt += f" The repository is already checked out at {repo_path}."
    prompt += " Follow the SWE workflow in your instructions exactly."
    return await SWEAgent.run(prompt, verbose=verbose, ticket=ticket_key)
