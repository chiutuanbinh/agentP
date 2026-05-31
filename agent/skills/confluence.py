"""Confluence skill — wiki search and retrieval via wiki_client.py."""

from pathlib import Path

from ._base import Skill

_AGENT_DIR = Path(__file__).parent.parent

CONFLUENCE = Skill(
    name="confluence",
    tools=("Bash",),
    prompt_section=f"""\
## Confluence wiki (run from {_AGENT_DIR})
Always prefix: `cd {_AGENT_DIR} && python wiki_client.py ...`

### Read
- `python wiki_client.py search <query> [space_key]` — full-text search
- `python wiki_client.py get <page_id>` — fetch page by ID
- `python wiki_client.py get-by-title <SPACE> <Page Title>` — fetch by exact title

### Write
- `python wiki_client.py create <SPACE> <Title> <body_html> [parent_id]` — create page
- `python wiki_client.py update <page_id> <Title> <body_html> <version>` — update page
  (get current version from `get` first)

Body must be Confluence storage XML. Minimal example:
```xml
<p>Paragraph text.</p>
<h2>Section</h2>
<ul><li>Item one</li><li>Item two</li></ul>
```
For ADRs: fetch the page first (to get version number), then update with incremented version.

Search before implementing — find ADRs, design docs, runbooks, and API specs.
""",
)
