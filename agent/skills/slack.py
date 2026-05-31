"""Slack skill — post notifications via webhook or CLI."""

from ._base import Skill

SLACK = Skill(
    name="slack",
    tools=("Bash",),
    prompt_section="""\
## Slack notifications
Post completion/failure messages to Slack.

### Webhook (preferred — set SLACK_WEBHOOK_URL env var)
```bash
curl -s -X POST "$SLACK_WEBHOOK_URL" \
  -H 'Content-type: application/json' \
  --data '{"text": "Agent finished: <message>"}'
```

### Slack CLI (if installed and authenticated)
```bash
slack message send --channel "#channel" --message "text"
```

Use webhooks when SLACK_WEBHOOK_URL is set. Skip silently if neither is available.
Always notify on: task completion with result summary, unrecoverable errors.
""",
)
