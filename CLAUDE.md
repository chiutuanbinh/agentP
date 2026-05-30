# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run any script
uv run <script.py>

# Add dependency
uv add <package>

# Lint
uv run ruff check .
uv run ruff format .

# Run ADK agent (web UI)
uv run adk web adk/
```

## Architecture

Repo experiments with two AI agent frameworks side-by-side:

**`adk/`** — Google ADK agents (`google-adk`). Entry point is `root_agent` in `adk/agent.py`. Run via `adk web`. Session state persisted in `adk/.adk/session.db`.

**`claude/`** — Anthropic Claude experiments:
- `llm_api.py` — direct Anthropic Messages API (`anthropic` SDK)
- `agent_sdk.py` — Claude Agent SDK (`claude-agent-sdk`), uses `query()` to spin up a Claude Code subprocess with tool access (`Read`, `Edit`, `Glob`) in `acceptEdits` permission mode
- `buggy.py` — sample target file used by `agent_sdk.py` for bug-review experiments

**`agent/`** — Containerized dev agent MVP:
- `Dockerfile` — `python:3.14-slim` image with `git`, `gh` CLI, `uv`, `anthropic`, `PyGithub`, `ruff`, `pytest`. No credentials baked in.
- Entry point: `/agent/run.py` (must be mounted or built into image at runtime)
- Build: `docker build -t dev-agent:local agent/`
- Run: `docker run --rm -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY -e GITHUB_TOKEN=$GITHUB_TOKEN -v /tmp/workspace:/workspace dev-agent:local`

**Runtime:** Python 3.14, `uv` for package/env management. `ANTHROPIC_API_KEY` required in `.env` for `claude/` scripts.
