"""PM agent — ticket management, spec writing, epic decomposition."""

from ..skills import CONFLUENCE, JIRA
from ._base import BaseAgent


class PMAgent(BaseAgent):
    AGENT_NAME = "pm"
    SKILLS = [JIRA, CONFLUENCE]


async def run(ticket_key: str, task: str = "review", verbose: bool = False) -> str:
    prompt = f"You are working on Jira ticket {ticket_key}. Task: {task}. Follow the PM workflow."
    return await PMAgent.run(prompt, verbose=verbose, ticket=ticket_key, task=task)
