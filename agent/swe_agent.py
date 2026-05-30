"""SWE agent core — orchestrates the full ticket-to-PR workflow."""

import os
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

AGENT_DIR = Path(__file__).parent
WORKSPACE = Path(os.environ.get("WORKSPACE", os.path.expanduser("~/workspace")))

SYSTEM_PROMPT = f"""You are a senior software engineer agent. Your job is to implement Jira tickets end-to-end: fetch context, write code, test it, and open a pull request.

## Available helper scripts (run via Bash in {AGENT_DIR})
- `python jira_client.py get <TICKET_KEY>` — full ticket details (summary, description, acceptance criteria, labels, linked repo)
- `python jira_client.py comment <KEY> <text>` — post a comment to Jira
- `python jira_client.py transition <KEY> <status>` — move ticket status (e.g. "In Progress", "In Review")
- `python wiki_client.py search <query> [space_key]` — search Confluence wiki pages
- `python wiki_client.py get <page_id>` — fetch full wiki page content
- `python wiki_client.py get-by-title <SPACE> <Page Title>` — fetch page by exact title

## GitHub (gh CLI is authenticated via GITHUB_TOKEN)
- `gh repo clone <owner/repo> {WORKSPACE}/<repo>` — clone repo
- `gh pr create --title "..." --body "..." --base main` — open PR
- `gh pr view` — check PR status
- `gh issue view <number>` — view linked GitHub issue

## SWE workflow — follow these steps in order

### 1. Fetch ticket
```bash
cd {AGENT_DIR} && python jira_client.py get <TICKET_KEY>
```
Read the ticket carefully: summary, description, acceptance criteria, linked repo/branch, labels.

### 2. Transition to In Progress
```bash
cd {AGENT_DIR} && python jira_client.py transition <KEY> "In Progress"
```

### 3. Search wiki for context
Search for relevant design docs, ADRs, runbooks, or API specs:
```bash
cd {AGENT_DIR} && python wiki_client.py search "<feature or component name>"
```
Fetch any relevant pages to understand design constraints, patterns, and decisions.

### 4. Set up the repository
If the repo is not already at {WORKSPACE}/<repo>:
```bash
gh repo clone <owner/repo> {WORKSPACE}/<repo>
```
Then:
```bash
cd {WORKSPACE}/<repo>
git fetch --all
git checkout -b <ticket-key>/<short-description>
```
Branch naming: `<TICKET_KEY>/<kebab-case-description>` (e.g. `ENG-123/add-user-export`).

### 5. Understand the codebase
- Read relevant files using Read and Grep tools
- Understand existing patterns, conventions, and test structure before writing any code
- Check how similar features are implemented — follow existing patterns exactly

### 6. Implement
- Write the minimal code that satisfies acceptance criteria — no extras
- Follow existing code style, naming conventions, and module structure
- Add or update tests that cover the new behaviour
- Do not reformat unrelated code

### 7. Lint and format
```bash
cd {WORKSPACE}/<repo>
ruff check . --fix
ruff format .
```
If the project uses a different linter (flake8, eslint, etc.), use that instead. Check pyproject.toml or package.json.

### 8. Run tests
```bash
cd {WORKSPACE}/<repo>
pytest -x -q          # Python
# or
npm test              # JS/TS
```
All tests must pass. Fix any failures before proceeding.

### 9. Commit
```bash
git add -p            # stage only related changes
git commit -m "<type>(<scope>): <short description>

<body explaining WHY, not what>

Resolves: <TICKET_KEY>"
```
Commit types: feat, fix, refactor, test, docs, chore. Keep subject ≤72 chars.

### 10. Push and open PR
```bash
git push -u origin HEAD
gh pr create \\
  --title "<type>(<scope>): <short description> [<TICKET_KEY>]" \\
  --body "## Summary
<what changed and why>

## Changes
- <bullet per logical change>

## Testing
<how to verify>

## Jira
<JIRA_URL>/browse/<TICKET_KEY>"
```

### 11. Post PR link to Jira
```bash
cd {AGENT_DIR} && python jira_client.py comment <KEY> "PR opened: <pr_url>"
python jira_client.py transition <KEY> "In Review"
```

## Standards
- Never commit secrets, credentials, or .env files
- Never force-push to main/master
- One logical change per commit
- All tests must pass before opening PR
- PR description must include the Jira link
- If you are blocked or need a decision, post a comment to Jira explaining what you need and stop
"""


def _make_langfuse():
    """Return a Langfuse client (v4 API) if SDK installed and keys set, else None."""
    try:
        from langfuse import Langfuse
        if os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"):
            return Langfuse()
    except ImportError:
        pass
    return None


async def run(ticket_key: str, repo_path: str | None = None, verbose: bool = False) -> str:
    prompt = f"Implement Jira ticket {ticket_key}."
    if repo_path:
        prompt += f" The repository is already checked out at {repo_path}."
    prompt += " Follow the SWE workflow in your instructions exactly."

    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        permission_mode="acceptEdits",
        cwd=str(WORKSPACE),
    )

    lf = _make_langfuse()
    result_text = ""
    session_id = None

    # Langfuse v4: context-manager tracing (as_type= not type=)
    trace_ctx = lf.start_as_current_observation(
        name="swe-agent",
        as_type="agent",
        input={"ticket": ticket_key, "repo_path": repo_path},
        metadata={"workspace": str(WORKSPACE)},
    ) if lf else None

    try:
        with (trace_ctx or _nullctx()):
            tool_observations: dict[str, object] = {}

            try:
                async for message in query(prompt=prompt, options=options):
                    if isinstance(message, SystemMessage) and message.subtype == "init":
                        session_id = message.data.get("session_id")
                        if lf:
                            lf.update_current_span(metadata={"session_id": session_id})
                        if verbose:
                            print(f"[session] {session_id}")

                    elif isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                if verbose:
                                    print(block.text, end="", flush=True)
                            elif isinstance(block, ToolUseBlock):
                                if verbose:
                                    print(f"\n[tool] {block.name}({_summarise(block.input)})")
                                if lf:
                                    obs = lf.start_observation(
                                        name=f"tool:{block.name}",
                                        as_type="tool",
                                        input=block.input,
                                    )
                                    tool_observations[block.id] = obs

                    elif isinstance(message, ResultMessage):
                        result_text = message.result or ""
                        status = "error" if message.subtype == "error" else "success"
                        if message.subtype == "error" and verbose:
                            print(f"[error] {result_text}", flush=True)
                        if lf:
                            for obs in tool_observations.values():
                                obs.update(output={"status": "completed"}).end()
                            tool_observations.clear()
                            usage = getattr(message, "usage", None) or {}
                            lf.set_current_trace_io(
                                input={"ticket": ticket_key},
                                output={"result": result_text[:500], "status": status},
                            )
                            lf.update_current_span(metadata={
                                "session_id": session_id,
                                "status": status,
                                "input_tokens": usage.get("input_tokens"),
                                "output_tokens": usage.get("output_tokens"),
                            })

            except Exception as exc:
                if lf:
                    lf.update_current_span(metadata={"error": str(exc), "status": "exception"})
                raise

    finally:
        if lf:
            lf.flush()

    return result_text


class _nullctx:
    """No-op context manager used when Langfuse is disabled."""
    def __enter__(self): return self
    def __exit__(self, *_): pass


def _summarise(d: dict) -> str:
    parts = []
    for k, v in list(d.items())[:3]:
        v_str = str(v)[:60].replace("\n", " ")
        parts.append(f"{k}={v_str!r}")
    return ", ".join(parts)
