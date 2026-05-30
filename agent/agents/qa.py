"""QA agent — test planning, PR review, bug reporting."""

from typing import ClassVar

from ..skills import GITHUB, JIRA, TESTING
from ._base import BaseAgent


class QAAgent(BaseAgent):
    AGENT_NAME = "qa"
    SKILLS: ClassVar[list] = [JIRA, GITHUB, TESTING]


async def run(ticket_key: str, pr_number: int | None = None, verbose: bool = False) -> str:
    prompt = f"QA review for Jira ticket {ticket_key}."
    if pr_number:
        prompt += (
            f" PR number: {pr_number}. Review the PR against the ticket's acceptance criteria."
        )
    else:
        prompt += " Write a test plan covering all acceptance criteria."
    return await QAAgent.run(prompt, verbose=verbose, ticket=ticket_key, pr=pr_number)
