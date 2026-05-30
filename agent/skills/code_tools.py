"""Code tools skill — linting, formatting, git workflow guidance."""

from ._base import Skill

CODE_TOOLS = Skill(
    name="code_tools",
    tools=("Read", "Write", "Edit", "Glob", "Grep"),
    prompt_section="""\
## Code tools
- Use Read/Grep/Glob to understand existing patterns before writing code
- Follow existing code style, naming conventions, and module structure exactly
- Linting: `ruff check . --fix && ruff format .` (Python); `eslint . --fix` (JS/TS)
- Check pyproject.toml or package.json for project-specific lint/format commands
- Never reformat unrelated code
- Commit messages: `<type>(<scope>): <subject>` — subject ≤72 chars; types: feat/fix/refactor/test/docs/chore
""",
)
