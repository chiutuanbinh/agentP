"""Confluence skill — wiki search and retrieval via wiki_client.py."""

from pathlib import Path

from ._base import Skill

_AGENT_DIR = Path(__file__).parent.parent

CONFLUENCE = Skill(
    name="confluence",
    tools=("Bash",),
    prompt_section=f"""\
## Confluence wiki (run from {_AGENT_DIR})
- `python wiki_client.py search <query> [space_key]` — full-text search
- `python wiki_client.py get <page_id>` — fetch page by ID
- `python wiki_client.py get-by-title <SPACE> <Page Title>` — fetch by exact title

Always prefix: `cd {_AGENT_DIR} && python wiki_client.py ...`
Search before implementing — find ADRs, design docs, runbooks, and API specs.
""",
)
