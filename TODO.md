# Agentic System TODO

## Done ✅

### Core infrastructure
- [x] `BaseAgent` — template method: prompt assembly, tool union, Langfuse tracing, SDK query loop
- [x] `Skill` base class — `prompt_section` + `tools` contract
- [x] Langfuse tracing — graceful no-op when keys absent; tool spans, usage metadata

### Agents (6)
- [x] `SWEAgent` — ticket → PR workflow; Jira + GitHub + Confluence + code tools + Slack
- [x] `PMAgent` — ticket mgmt, spec writing, epic decomp; Jira + Confluence
- [x] `QAAgent` — test planning, PR review, bug reporting; Jira + GitHub + testing + Slack
- [x] `ArchAgent` — design review, ADRs; Confluence + GitHub + code tools + Jira + Slack
- [x] `SecurityAgent` — vuln audit, findings, remediation tickets; GitHub + Jira + security_audit
- [x] `AgentBuilderAgent` — builds new agents; SDK docs + code tools + Langfuse

### Skills (9)
- [x] `jira` — fetch/comment/transition; hard-stop on non-zero exit
- [x] `github` — PR diff, review, gh CLI; hard-stop on non-zero exit
- [x] `confluence` — search/get/create/update; Confluence storage XML guidance included
- [x] `code_tools` — Read/Edit/Write/Bash/Glob/Grep
- [x] `testing` — test planning/execution
- [x] `security_audit` — OWASP audit patterns
- [x] `agent_builder_docs` — MCP-backed SDK doc access
- [x] `langfuse` — query traces/observations at runtime; wired to AgentBuilderAgent
- [x] `slack` — webhook + CLI notifications; wired to SWE/QA/Arch agents

### Prompts (6) — one `.md` per agent in `agent/prompts/`

### Tooling
- [x] `run.py` CLI — `--agent`, `--repo`, `--pr`, `--task`, `--verbose`, `--model`, `--dry-run`, `--timeout`
- [x] `jira_client.py` / `wiki_client.py` — CLI helpers (wiki: read + create/update)
- [x] `.env.example` — all env vars documented with descriptions
- [x] `ruff` post-edit hook — auto lint/format on `.py` save
- [x] CI — lint + format + `pytest tests/ -q` on every push/PR
- [x] MCP servers — `claude-sdk-docs`, `langfuse-docs`, `langfuse-official`
- [x] ADK experiment (`adk/`) — Google ADK agent side-by-side

### Testing
- [x] `tests/test_skills.py` — 10 tests: Skill dataclass, prompt assembly, tool dedup, dry_run

### Error handling / reliability
- [x] Timeout — `asyncio.wait_for`; default 600s, `--timeout` override
- [x] Retry — 3 attempts, exponential backoff on transient SDK errors
- [x] Cost tracking — `[tokens] input=N output=N` printed with `--verbose`
- [x] Tool result errors — jira/github skills instruct hard-stop on non-zero exit codes

### Agent improvements
- [x] `PMAgent.run()` role injection fixed
- [x] `SWEAgent` PR validation — step 10 runs `gh pr view` before posting to Jira
- [x] `AgentBuilderAgent` includes `LANGFUSE_SKILL`

### Langfuse API
- [x] `start_as_current_observation` verified present in Langfuse v4 SDK
- [x] Removed deprecated `set_current_trace_io` → `update_current_span(input=, output=)`

### CLI / DX
- [x] `--dry-run`, `--model`, `--timeout` flags
- [x] `swe_agent.py` shim removed; CLAUDE.md updated
- [x] `SLACK_WEBHOOK_URL` documented in CLAUDE.md and `.env.example`
