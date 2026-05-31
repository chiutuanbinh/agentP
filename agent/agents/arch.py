"""Architecture agent — design review, ADR writing, systemic code issues."""

from typing import ClassVar

from ..skills import CODE_TOOLS, CONFLUENCE, GITHUB, JIRA, SLACK
from ._base import BaseAgent


class ArchAgent(BaseAgent):
    AGENT_NAME = "arch"
    SKILLS: ClassVar[list] = [CONFLUENCE, GITHUB, CODE_TOOLS, JIRA, SLACK]


async def run(
    ticket_key: str,
    pr_number: int | None = None,
    verbose: bool = False,
    model: str | None = None,
    dry_run: bool = False,
    timeout: float | None = 600.0,
) -> str:
    prompt = f"Architecture review for Jira ticket {ticket_key}."
    if pr_number:
        prompt += f" Review PR #{pr_number} for architectural concerns."
    else:
        prompt += (
            " Fetch the ticket, search wiki for relevant ADRs, and write an architecture review."
        )
    return await ArchAgent.run(
        prompt,
        verbose=verbose,
        model=model,
        dry_run=dry_run,
        timeout=timeout,
        ticket=ticket_key,
        pr=pr_number,
    )
