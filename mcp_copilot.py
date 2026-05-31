"""MCP server exposing GitHub Copilot SDK as tools for agent_builder."""

import asyncio
import json
import os

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("copilot-sdk")

_GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")


def _run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result(timeout=120)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@mcp.tool()
def copilot_list_models() -> str:
    """List available models from GitHub Copilot."""

    async def _list():
        from copilot import CopilotClient

        async with CopilotClient(github_token=_GITHUB_TOKEN) as client:
            models = await client.list_models()
            return json.dumps([m if isinstance(m, str) else vars(m) for m in models], default=str)

    return _run(_list())


@mcp.tool()
def copilot_chat(
    message: str,
    model: str = "gpt-4o",
    system_message: str | None = None,
) -> str:
    """Send a message to GitHub Copilot and return the response.

    Args:
        message: The user message to send.
        model: Model to use (e.g. gpt-4o, claude-sonnet-4.5, gpt-5).
        system_message: Optional system message to prepend.
    """

    async def _chat():
        from copilot import CopilotClient
        from copilot.generated.session_events import AssistantMessageData, SessionIdleData
        from copilot.session import PermissionHandler

        create_kwargs = {
            "on_permission_request": PermissionHandler.approve_all,
            "model": model,
            "infinite_sessions": {"enabled": False},
        }
        if system_message:
            create_kwargs["system_message"] = {"text": system_message}

        response_parts: list[str] = []
        done = asyncio.Event()

        client_cm = CopilotClient(github_token=_GITHUB_TOKEN)
        async with client_cm as client, await client.create_session(**create_kwargs) as session:

            def on_event(event):
                match event.data:
                    case AssistantMessageData() as data:
                        response_parts.append(data.content)
                    case SessionIdleData():
                        done.set()

            session.on(on_event)
            await session.send(message)
            await asyncio.wait_for(done.wait(), timeout=60)

        return "\n".join(response_parts) if response_parts else "(no response)"

    return _run(_chat())


@mcp.tool()
def copilot_chat_with_tools(
    message: str,
    tools_json: str,
    model: str = "gpt-4o",
) -> str:
    """Send a message to Copilot with custom tool definitions (declaration-only).

    Returns the full response including any tool call requests as JSON.

    Args:
        message: The user message to send.
        tools_json: JSON array of tool definitions. Each: {"name", "description", "parameters"}.
        model: Model to use.
    """

    async def _chat_tools():
        import json as _json

        from copilot import CopilotClient
        from copilot.generated.session_events import (
            AssistantMessageData,
            SessionIdleData,
        )
        from copilot.session import PermissionHandler
        from copilot.tools import Tool

        tool_defs = _json.loads(tools_json)
        tools = [
            Tool(
                name=t["name"],
                description=t["description"],
                parameters=t["parameters"],
                handler=None,
            )
            for t in tool_defs
        ]

        events: list[dict] = []
        done = asyncio.Event()

        async with (
            CopilotClient(github_token=_GITHUB_TOKEN) as client,
            await client.create_session(
                on_permission_request=PermissionHandler.approve_all,
                model=model,
                tools=tools,
                infinite_sessions={"enabled": False},
            ) as session,
        ):

            def on_event(event):
                data = event.data
                events.append({"type": event.type, "data": str(data)})
                match data:
                    case AssistantMessageData():
                        pass
                    case SessionIdleData():
                        done.set()

            session.on(on_event)
            await session.send(message)
            await asyncio.wait_for(done.wait(), timeout=60)

        return _json.dumps(events, indent=2)

    return _run(_chat_tools())


if __name__ == "__main__":
    mcp.run()
