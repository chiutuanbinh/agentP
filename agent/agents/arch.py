"""Architecture agent — design review, ADR writing, systemic code issues."""

from ..skills import CODE_TOOLS, CONFLUENCE, GITHUB, JIRA
from ._base import BaseAgent


class ArchAgent(BaseAgent):
    AGENT_NAME = "arch"
    SKILLS = [CONFLUENCE, GITHUB, CODE_TOOLS, JIRA]


async def run(
    ticket_key: str, pr_number: int | None = None, verbose: bool = False
) -> str:
    prompt = f"Architecture review for Jira ticket {ticket_key}."
    if pr_number:
        prompt += f" Review PR #{pr_number} for architectural concerns."
    else:
        prompt += " Fetch the ticket, search wiki for relevant ADRs, and write an architecture review."
    return await ArchAgent.run(prompt, verbose=verbose, ticket=ticket_key, pr=pr_number)
