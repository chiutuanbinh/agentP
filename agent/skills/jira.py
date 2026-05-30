"""Jira skill — ticket CRUD via jira_client.py."""

from pathlib import Path

from ._base import Skill

_AGENT_DIR = Path(__file__).parent.parent

JIRA = Skill(
    name="jira",
    tools=("Bash",),
    prompt_section=f"""\
## Jira (run from {_AGENT_DIR})
- `python jira_client.py get <KEY>` — full ticket (summary, description, AC, labels, linked repo)
- `python jira_client.py search <jql>` — JQL search
- `python jira_client.py comment <KEY> <text>` — post comment
- `python jira_client.py transition <KEY> <status>`
  — move status: "In Progress", "In Review", "Done"

Always prefix commands: `cd {_AGENT_DIR} && python jira_client.py ...`
""",
)
