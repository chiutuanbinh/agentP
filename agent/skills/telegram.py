"""Telegram skill — send notifications via Telegram Bot API."""

from ._base import Skill

TELEGRAM = Skill(
    name="telegram",
    tools=("Bash",),
    prompt_section="""\
## Telegram notifications
Send messages to Telegram via bot @agentBCT_bot (t.me/agentBCT_bot).
Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars.

### Send message
```bash
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \\
  -H 'Content-Type: application/json' \\
  -d "{\"chat_id\": \"${TELEGRAM_CHAT_ID}\", \"text\": \"<message>\", \"parse_mode\": \"Markdown\"}"
```

### Send with HTML formatting
```bash
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \\
  -H 'Content-Type: application/json' \\
  -d "{\"chat_id\": \"${TELEGRAM_CHAT_ID}\", \"text\": \"<message>\", \"parse_mode\": \"HTML\"}"
```

Use Markdown for bold (`*text*`), code (`` `code` ``), links (`[label](url)`).
Skip silently if TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set.
Always notify on: task completion with result summary, unrecoverable errors.
""",
)
