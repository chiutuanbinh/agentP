# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git workflow

Every task: create fresh branch from default branch → make changes → open PR. Never commit directly to main or any other existing branch.

## Commands

```bash
# Run any script
uv run <script.py>

# Add dependency
uv add <package>

# Lint / format
uv run ruff check .
uv run ruff format .

# Run ADK agent (web UI)
uv run adk web adk/

# Run SWE agent against a Jira ticket
uv run python agent/run.py <TICKET-KEY> --verbose

# Build SWE agent Docker image
docker build -t swe-agent:local agent/

# Run SWE agent in Docker
docker run --rm \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e GITHUB_TOKEN=$GITHUB_TOKEN \
  -e JIRA_URL=$JIRA_URL \
  -e JIRA_USER=$JIRA_USER \
  -e JIRA_API_TOKEN=$JIRA_API_TOKEN \
  -v /tmp/workspace:/workspace \
  swe-agent:local python run.py <TICKET-KEY>
```

## Architecture

1 experiment directory:

**`agent/`** — Multi-agent system: ticket → PR workflow using Claude Agent SDK.
- `run.py` — CLI entry; validates env, loads `.env`, dispatches to agent type (`--agent agent_builder|arch|pm|qa|security|swe`)
- `agents/_base.py` — `BaseAgent`: template method for prompt assembly, tool union, Langfuse tracing, backend dispatch
- `agents/{...}.py` — one class + `run()` per agent type (see below)
- `backends/{...}.py` — LLMBackend strategy layer: `adk`, `claude`, `copilot`
- `skills/{...}.py` — composable skill units (tools + prompt section)
- `prompts/{...}.md` — system prompts, one per agent
- `jira_client.py` — Jira REST API CLI; agent invokes via `Bash`: `python jira_client.py get|search|comment|transition <args>`
- `wiki_client.py` — Confluence REST API CLI; agent invokes via `Bash`: `python wiki_client.py search|get|get-by-title <args>`

**Agents** (`agent/agents/`):
- `agent_builder.py` (`agent_builder`) — Agent builder — creates new agents using Claude Agent SDK and Langfuse docs
- `arch.py` (`arch`) — Architecture agent — design review, ADR writing, systemic code issues
- `pm.py` (`pm`) — PM agent — ticket management, spec writing, epic decomposition
- `qa.py` (`qa`) — QA agent — test planning, PR review, bug reporting
- `security.py` (`security`) — Security agent — vulnerability audit, findings, remediation tickets
- `swe.py` (`swe`) — SWE agent — ticket-to-PR workflow

**Backends** (`agent/backends/`) — LLMBackend strategy:
- `adk.py` (`name="adk"`) — ADK backend — runs agents via Google ADK (Gemini models)
- `claude.py` (`name="claude"`) — Claude backend — runs agents via Claude Agent SDK (claude-code subprocess)
- `copilot.py` (`name="copilot"`) — Copilot backend — runs agents via GitHub Copilot SDK

**Skills** (`agent/skills/`) — composable tool + prompt units:
- `agent_builder_docs.py` (`agent_builder_docs`) — Agent builder docs skill — MCP tools for Claude Agent SDK and Langfuse docs
- `code_tools.py` (`code_tools`) — Code tools skill — linting, formatting, git workflow guidance
- `confluence.py` (`confluence`) — Confluence skill — wiki search and retrieval via wiki_client.py
- `copilot.py` (`copilot`) — GitHub Copilot SDK skill — MCP tools for interacting with GitHub Copilot
- `github.py` (`github`) — GitHub skill — gh CLI interactions
- `jira.py` (`jira`) — Jira skill — ticket CRUD via jira_client.py
- `langfuse.py` (`langfuse`) — Langfuse skill — query traces and observations at runtime
- `security_audit.py` (`security_audit`) — Security audit skill — vulnerability review and audit guidance
- `slack.py` (`slack`) — Slack skill — post notifications via webhook or CLI
- `telegram.py` (`telegram`) — Telegram skill — send notifications via Telegram Bot API
- `testing.py` (`testing`) — Testing skill — test writing, coverage, and QA guidance

**MCP servers** (root):
- `mcp_claude_docs.py` (`claude-sdk-docs`) — MCP server for fetching live Claude SDK documentation
- `mcp_copilot.py` (`copilot-sdk`) — MCP server exposing GitHub Copilot SDK as tools for agent_builder
- `mcp_langfuse_docs.py` (`langfuse-docs`) — MCP server for Langfuse documentation and local OpenAPI spec

**Scripts** (`scripts/`):
- `sync_agents.py` — Sync agent/ Python definitions → .claude/agents/*.md
- `update_claude_md.py` — Regenerate the Architecture section of CLAUDE.md from current codebase state
## Environment variables

Required for `agent/`:
```
ANTHROPIC_API_KEY
JIRA_URL          # e.g. https://yourco.atlassian.net
JIRA_USER         # email
JIRA_API_TOKEN
GITHUB_TOKEN
```

Optional:
```
LANGFUSE_PUBLIC_KEY   # enables Langfuse tracing
LANGFUSE_SECRET_KEY
LANGFUSE_HOST         # default: https://cloud.langfuse.com; use http://localhost:3000 for local
CONFLUENCE_URL        # falls back to JIRA_URL if unset
CONFLUENCE_USER       # falls back to JIRA_USER
CONFLUENCE_API_TOKEN  # falls back to JIRA_API_TOKEN
WORKSPACE             # repo checkout root; defaults to ~/workspace
SLACK_WEBHOOK_URL     # enables Slack notifications (incoming webhook URL)
```

## Hooks

`.claude/settings.json` registers a `PostToolUse` hook that runs `uv run ruff check --fix` on any `.py` file after `Edit` or `Write`.

## Prompt Standards

All prompts in `agent/prompts/` and user prompts in `agent/agents/` must follow these rules.

### System prompts (`agent/prompts/<name>.md`)

- **Role first** — first line: `You are a <role>. Your job is to <goal>.`
- **XML tags** — wrap major blocks: `<workflow>`, `<standards>`, `<output_format>`, `<examples>`
- **Output format explicit** — define expected output shape (JSON, markdown structure, or example)
- **Failure mode** — always include: "If blocked or insufficient context, [action] and stop."
- **No runtime values** — use `{PLACEHOLDER}` tokens for values injected at runtime (e.g. `{WORKSPACE}`)

### User prompts (in `agent/agents/*.py`)

- **Task only** — no role assignment; role lives in system prompt
- **Structured** — `f"Ticket: {key}. Task: {task}. [constraints]."` — explicit fields, no prose
- **Output anchor** — if response format matters, state it: `"Return JSON: {status, findings[]}"`

### Skill `prompt_section` (`agent/skills/*.py`)

Each `Skill.prompt_section` is injected verbatim into system prompt — treat it as a system prompt fragment.

- **Header required** — start with `## <Skill name>` so agent knows section boundary
- **Commands exact** — CLI commands must be copy-pasteable; include working directory prefix when needed (see `jira.py`, `confluence.py`)
- **Action verbs** — instructions as imperatives: "Use X for Y", "Never Z", "Always prefix..."
- **No prose filler** — no "This skill provides...", "You can use..." — just the rules
- **Failure/constraint explicit** — if tool unavailable or forbidden action exists, state it (e.g. "Never commit exploit payloads")
- **Single responsibility** — one skill = one external system or capability; no cross-skill logic

Skill review findings use same caveman-review format:

```
agent/skills/foo.py:L<n>: 🔴 bug: <problem>. <fix>.
agent/skills/foo.py:L<n>: 🟡 risk: <problem>. <fix>.
agent/skills/foo.py:L<n>: 🔵 nit: <problem>. <fix>.
```

---

### Comment format for prompt review findings

One line per finding: `<file>:L<line>: <🔴|🟡|🔵|❓> <type>: <problem>. <fix>. [<ref>]`

- `🔴 bug:` — wrong output, injection surface, dead placeholder, role in wrong prompt
- `🟡 risk:` — no failure fallback, ambiguous instruction, missing output format
- `🔵 nit:` — best-practice gap (no XML tags, vague verb, no example)
- `❓ q:` — intent unclear

References: [Anthropic prompt engineering](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview) · [XML tags](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags) · [chain prompts](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/chain-prompts)

---

## Local Langfuse

```bash
curl -o /tmp/langfuse-compose.yml https://raw.githubusercontent.com/langfuse/langfuse/main/docker-compose.yml
docker compose -f /tmp/langfuse-compose.yml up -d
# UI at http://localhost:3000
```

