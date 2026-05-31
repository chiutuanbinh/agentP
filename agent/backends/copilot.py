"""Copilot backend — runs agents via GitHub Copilot SDK."""

import asyncio
import os

from ._base import BackendResult, LLMBackend

_DEFAULT_MODEL = "gpt-4o"


class CopilotBackend(LLMBackend):
    """Execute agent tasks through GitHub Copilot CLI.

    `allowed_tools` from skills are ignored — Copilot manages its own built-in
    tool set (read_file, edit_file, run_terminal, etc.) via approve_all.
    `system_prompt` is passed as Copilot session system_message.
    """

    name = "copilot"

    async def run(
        self,
        prompt: str,
        system_prompt: str,
        allowed_tools: list[str],
        model: str | None,
        cwd: str,
        verbose: bool,
        timeout: float | None,
        langfuse: object | None,
        trace_meta: dict,
        mcp_servers: dict,
    ) -> BackendResult:
        from copilot import CopilotClient
        from copilot.generated.session_events import (
            AssistantMessageData,
            SessionIdleData,
        )
        from copilot.session import PermissionHandler

        github_token = os.environ.get("GITHUB_TOKEN")
        effective_model = model or _DEFAULT_MODEL

        response_parts: list[str] = []
        tool_calls: list[str] = []
        done = asyncio.Event()

        create_kwargs: dict = {
            "on_permission_request": PermissionHandler.approve_all,
            "model": effective_model,
            "infinite_sessions": {"enabled": False},
            "system_message": {"text": system_prompt},
            "hooks": {
                "on_pre_tool_use": _make_pre_tool_hook(tool_calls, verbose),
                "on_post_tool_use": _make_post_tool_hook(verbose),
                "on_post_tool_use_failure": _make_failure_hook(verbose),
            },
        }

        client_kwargs: dict = {
            "working_directory": cwd,
        }
        if github_token:
            client_kwargs["github_token"] = github_token

        if verbose:
            print(f"[copilot] model={effective_model} cwd={cwd}")  # noqa: T201

        async def _run():
            client_cm = CopilotClient(**client_kwargs)
            async with client_cm as client, await client.create_session(**create_kwargs) as session:

                def on_event(event):
                    match event.data:
                        case AssistantMessageData() as data:
                            response_parts.append(data.content)
                            if verbose:
                                print(data.content, end="", flush=True)  # noqa: T201
                        case SessionIdleData():
                            done.set()

                session.on(on_event)
                await session.send(prompt)
                await asyncio.wait_for(done.wait(), timeout=timeout)

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                await _run()
                break
            except TimeoutError:
                if langfuse:
                    langfuse.update_current_span(
                        metadata={"error": "timeout", "status": "timeout", "backend": self.name}
                    )
                raise
            except Exception as exc:
                if attempt == max_attempts:
                    if langfuse:
                        langfuse.update_current_span(
                            metadata={
                                "error": str(exc),
                                "status": "exception",
                                "backend": self.name,
                            }
                        )
                    raise
                wait = 2**attempt
                if verbose:
                    print(f"[copilot][retry {attempt}/{max_attempts - 1}] {exc} — retry in {wait}s")  # noqa: T201
                await asyncio.sleep(wait)
                done.clear()

        result_text = "\n".join(response_parts)
        if verbose:
            print(f"\n[copilot] tools used: {tool_calls}")  # noqa: T201

        if langfuse:
            langfuse.update_current_span(
                input={"prompt": prompt[:200], **trace_meta},
                output={"result": result_text[:500], "status": "success"},
                metadata={
                    "backend": self.name,
                    "model": effective_model,
                    "tool_calls": tool_calls,
                },
            )

        return BackendResult(
            text=result_text,
            session_id=None,
            backend=self.name,
            tool_calls=tool_calls,
        )


def _make_pre_tool_hook(tool_calls: list[str], verbose: bool):
    async def on_pre_tool_use(input, invocation):
        name = input.get("toolName", "?")
        tool_calls.append(name)
        if verbose:
            print(f"\n[copilot][tool] {name}")  # noqa: T201
        return {"permissionDecision": "allow"}

    return on_pre_tool_use


def _make_post_tool_hook(verbose: bool):
    async def on_post_tool_use(input, invocation):
        if verbose:
            print(f"[copilot][tool done] {input.get('toolName', '?')}")  # noqa: T201
        return {}

    return on_post_tool_use


def _make_failure_hook(verbose: bool):
    async def on_post_tool_use_failure(input, invocation):
        if verbose:
            print(f"[copilot][tool fail] {input.get('toolName', '?')}: {input.get('error', '')}")  # noqa: T201
        return {}

    return on_post_tool_use_failure
