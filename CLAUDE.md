# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

Three agent experiments side-by-side:

**`adk/`** — Google ADK agent (`google-adk`). Entry: `root_agent` in `adk/agent.py`. Run via `adk web`. Session state in `adk/.adk/session.db` (gitignored).

**`claude/`** — Anthropic Claude experiments:
- `llm_api.py` — direct Messages API (`anthropic` SDK)
- `agent_sdk.py` — Claude Agent SDK `query()`, spins up Claude Code subprocess with `Read`/`Edit`/`Glob` tools in `acceptEdits` mode
- `buggy.py` — sample target for `agent_sdk.py` bug-review experiments

**`agent/`** — Production SWE agent: ticket → PR workflow using Claude Agent SDK.
- `run.py` — CLI entry; validates env, loads `.env`, calls `swe_agent.run()`
- `swe_agent.py` — core: `query()` with a detailed SWE system prompt; Langfuse v4 tracing (graceful no-op if keys absent); `WORKSPACE` env var sets repo checkout dir (defaults to `~/workspace`)
- `jira_client.py` — Jira REST API CLI; agent invokes via `Bash`: `python jira_client.py get|search|comment|transition <args>`
- `wiki_client.py` — Confluence REST API CLI; agent invokes via `Bash`: `python wiki_client.py search|get|get-by-title <args>`
- Agent uses only built-in SDK tools (`Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`); external systems (Jira, GitHub via `gh` CLI, Confluence) accessed through `Bash` subprocess calls to the helper scripts

**`mcp_claude_docs.py`** — MCP server for Claude Agent SDK docs (registered in `.mcp.json` as `claude-sdk-docs`).

**`mcp_langfuse_docs.py`** — MCP server for Langfuse docs + local OpenAPI spec (registered as `langfuse-docs`). `.mcp.json` also registers `langfuse-official` (remote HTTP MCP at `https://langfuse.com/api/mcp`).

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
