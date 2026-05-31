"""GitHub Copilot SDK skill — MCP tools for interacting with GitHub Copilot."""

from ._base import Skill

COPILOT_SKILL = Skill(
    name="copilot",
    tools=(
        "mcp__copilot-sdk__copilot_list_models",
        "mcp__copilot-sdk__copilot_chat",
        "mcp__copilot-sdk__copilot_chat_with_tools",
    ),
    prompt_section="""\
## GitHub Copilot SDK
Use these tools to interact with GitHub Copilot programmatically via the Copilot Python SDK.

- `mcp__copilot-sdk__copilot_list_models` — list all available Copilot models
- `mcp__copilot-sdk__copilot_chat` — send a message to Copilot; returns assistant response
  - params: message (str), model (str, default gpt-4o), system_message (str | None)
  - supported models include: gpt-4o, gpt-5, claude-sonnet-4.5
- `mcp__copilot-sdk__copilot_chat_with_tools` — chat with declaration-only custom tools;
  returns raw JSON event stream including tool_call requests
  - params: message (str), tools_json (JSON array of {name, description, parameters}), model

Requires: GITHUB_TOKEN env var set with Copilot access.
If Copilot CLI not installed or token missing, tools will error — handle gracefully.
""",
)
