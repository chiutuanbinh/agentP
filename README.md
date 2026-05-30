# agentP

Multi-agent system for autonomous software engineering. Agents take Jira tickets end-to-end: fetch context, write code, open PRs, and report back.

## Agents

| Agent | Role |
|-------|------|
| `SWEAgent` | Implements tickets → opens PRs |
| `PMAgent` | Manages specs, epics, ticket decomposition |
| `QAAgent` | Test planning, PR review against acceptance criteria |
| `SecurityAgent` | Vulnerability audit, CVE triage, remediation tickets |
| `ArchAgent` | Design review, ADR writing, architecture lens on PRs |

Each agent is composed from **Skills** — pluggable units of tools + prompt guidance (Jira, GitHub, Confluence, code tools, testing, security audit).

## Usage

```bash
# Install deps
uv sync

# Run SWE agent against a Jira ticket
uv run python agent/run.py ENG-123 --verbose

# Docker
docker build -t swe-agent:local agent/
docker run --rm \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e GITHUB_TOKEN=$GITHUB_TOKEN \
  -e JIRA_URL=$JIRA_URL \
  -e JIRA_USER=$JIRA_USER \
  -e JIRA_API_TOKEN=$JIRA_API_TOKEN \
  -v /tmp/workspace:/workspace \
  swe-agent:local python run.py ENG-123
```

## Environment variables

```
ANTHROPIC_API_KEY
JIRA_URL              # https://yourco.atlassian.net
JIRA_USER             # email
JIRA_API_TOKEN
GITHUB_TOKEN

# Optional
LANGFUSE_PUBLIC_KEY   # enables tracing
LANGFUSE_SECRET_KEY
LANGFUSE_HOST         # default: https://cloud.langfuse.com
CONFLUENCE_URL        # falls back to JIRA_URL
WORKSPACE             # repo checkout root; default: ~/workspace
```

## Other experiments

**`adk/`** — Google ADK agent. Run: `uv run adk web adk/`

**`claude/`** — Anthropic SDK experiments: direct Messages API, Agent SDK, bug-review demo.

## License

MIT
