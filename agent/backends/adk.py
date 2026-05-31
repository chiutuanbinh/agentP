"""ADK backend — runs agents via Google ADK (Gemini models)."""

import os
import uuid

from google.adk.agents import Agent
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from ._base import BackendResult, LLMBackend

_DEFAULT_MODEL = "gemini-2.0-flash"


class ADKBackend(LLMBackend):
    """Execute agent tasks through Google ADK with Gemini models.

    `allowed_tools` from skills are ignored — ADK manages its own tool set.
    `system_prompt` becomes the agent instruction.
    """

    name = "adk"

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
        import asyncio

        effective_model = model or os.environ.get("ADK_MODEL", _DEFAULT_MODEL)

        agent = Agent(
            name="agent",
            model=effective_model,
            description="Multi-purpose agent",
            instruction=system_prompt,
            tools=[],
        )

        session_service = InMemorySessionService()
        runner = Runner(
            agent=agent,
            app_name="agent-runner",
            session_service=session_service,
        )

        user_id = "user"
        session_id = str(uuid.uuid4())
        session_service.create_session(
            app_name="agent-runner",
            user_id=user_id,
            session_id=session_id,
        )

        message = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=prompt)],
        )

        response_parts: list[str] = []
        tool_calls: list[str] = []
        input_tokens = 0
        output_tokens = 0

        if verbose:
            print(f"[adk] model={effective_model} session={session_id}")  # noqa: T201

        async def _run():
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=message,
            ):
                _handle_event(event, response_parts, tool_calls, verbose)

        if timeout:
            await asyncio.wait_for(_run(), timeout=timeout)
        else:
            await _run()

        result_text = "\n".join(response_parts)

        if verbose:
            print(f"\n[adk] tools used: {tool_calls}")  # noqa: T201

        if langfuse:
            langfuse.update_current_span(
                input={"prompt": prompt[:200], **trace_meta},
                output={"result": result_text[:500], "status": "success"},
                metadata={
                    "backend": self.name,
                    "model": effective_model,
                    "tool_calls": tool_calls,
                    "session_id": session_id,
                },
            )

        return BackendResult(
            text=result_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            session_id=session_id,
            backend=self.name,
            tool_calls=tool_calls,
        )


def _handle_event(
    event: Event,
    response_parts: list[str],
    tool_calls: list[str],
    verbose: bool,
) -> None:
    # Collect function calls for tracing
    for fc in event.get_function_calls() or []:
        tool_calls.append(fc.name)
        if verbose:
            print(f"\n[adk][tool] {fc.name}")  # noqa: T201

    # Extract text from final response only
    if event.is_final_response() and event.content:
        for part in event.content.parts or []:
            if part.text:
                response_parts.append(part.text)
                if verbose:
                    print(part.text, end="", flush=True)  # noqa: T201

    # Token usage
    usage = getattr(event, "usage_metadata", None)
    if usage and verbose:
        inp = getattr(usage, "prompt_token_count", 0) or 0
        out = getattr(usage, "candidates_token_count", 0) or 0
        if inp or out:
            print(f"\n[adk][tokens] input={inp} output={out}")  # noqa: T201
