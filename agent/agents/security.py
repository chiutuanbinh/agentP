"""Security agent — vulnerability audit, findings, remediation tickets."""

from typing import ClassVar

from ..skills import GITHUB, JIRA, SECURITY_AUDIT
from ._base import BaseAgent


class SecurityAgent(BaseAgent):
    AGENT_NAME = "security"
    SKILLS: ClassVar[list] = [GITHUB, SECURITY_AUDIT, JIRA]


async def run(
    ticket_key: str | None = None,
    pr_number: int | None = None,
    repo: str | None = None,
    verbose: bool = False,
    model: str | None = None,
    dry_run: bool = False,
    timeout: float | None = 600.0,
) -> str:
    parts = ["Security audit."]
    if ticket_key:
        parts.append(f"Jira ticket: {ticket_key}.")
    if pr_number:
        parts.append(f"PR #{pr_number}: fetch the diff and audit all changed files.")
    if repo:
        parts.append(f"Repository: {repo}. Audit the full codebase.")
    parts.append(
        "Report all findings with severity, location, and remediation. Create Jira tickets for high/critical."  # noqa: E501
    )
    prompt = " ".join(parts)
    return await SecurityAgent.run(
        prompt,
        verbose=verbose,
        model=model,
        dry_run=dry_run,
        timeout=timeout,
        ticket=ticket_key,
        pr=pr_number,
        repo=repo,
    )
