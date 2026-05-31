"""GitHub skill — gh CLI interactions."""

from ._base import Skill

GITHUB = Skill(
    name="github",
    tools=("Bash",),
    prompt_section="""\
## GitHub (gh CLI authenticated via GITHUB_TOKEN)
- `gh repo clone <owner/repo> <dest>` — clone repo
- `gh pr create --title "..." --body "..." --base main` — open PR
- `gh pr view [<number>]` — PR status
- `gh pr diff [<number>]` — PR diff
- `gh issue view <number>` — view issue
- `gh issue list --repo <owner/repo>` — list issues
- `gh api repos/<owner>/<repo>/pulls/<number>/reviews` — fetch PR reviews

If any `gh` command exits non-zero: stop, report the exact error, do not proceed.
""",
)
