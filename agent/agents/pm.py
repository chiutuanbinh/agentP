"""PM agent — ticket management, spec writing, epic decomposition."""

from typing import ClassVar

from ..skills import CONFLUENCE, JIRA
from ._base import BaseAgent


class PMAgent(BaseAgent):
    AGENT_NAME = "pm"
    SKILLS: ClassVar[list] = [JIRA, CONFLUENCE]


async def run(
    ticket_key: str,
    task: str = "review",
    verbose: bool = False,
    model: str | None = None,
    dry_run: bool = False,
    timeout: float | None = 600.0,
) -> str:
    prompt = f"Ticket: {ticket_key}. Task: {task}."
    return await PMAgent.run(
        prompt,
        verbose=verbose,
        model=model,
        dry_run=dry_run,
        timeout=timeout,
        ticket=ticket_key,
        task=task,
    )
