"""Claude backend — runs agents via Claude Agent SDK (claude-code subprocess)."""

import asyncio

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

from ._base import BackendResult, LLMBackend


class ClaudeBackend(LLMBackend):
    name = "claude"

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
        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            allowed_tools=allowed_tools,
            permission_mode="acceptEdits",
            cwd=cwd,
            model=model,
            mcp_servers=mcp_servers or {},
        )

        result_text = ""
        session_id = None
        tool_calls: list[str] = []
        tool_obs: dict[str, object] = {}
        input_tokens = 0
        output_tokens = 0

        async def _run_query():
            nonlocal result_text, session_id, input_tokens, output_tokens

            async for message in query(prompt=prompt, options=options):
                if isinstance(message, SystemMessage) and message.subtype == "init":
                    session_id = message.data.get("session_id")
                    if langfuse:
                        langfuse.update_current_span(metadata={"session_id": session_id})
                    if verbose:
                        print(f"[claude][session] {session_id}")  # noqa: T201

                elif isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            if verbose:
                                print(block.text, end="", flush=True)  # noqa: T201
                        elif isinstance(block, ToolUseBlock):
                            tool_calls.append(block.name)
                            if verbose:
                                print(f"\n[claude][tool] {block.name}({_summarise(block.input)})")  # noqa: T201
                            if langfuse:
                                obs = langfuse.start_observation(
                                    name=f"tool:{block.name}",
                                    as_type="tool",
                                    input=block.input,
                                )
                                tool_obs[block.id] = obs

                elif isinstance(message, ResultMessage):
                    result_text = message.result or ""
                    usage = getattr(message, "usage", None) or {}
                    input_tokens = usage.get("input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)
                    status = "error" if message.subtype == "error" else "success"
                    if message.subtype == "error" and verbose:
                        print(f"[claude][error] {result_text}", flush=True)  # noqa: T201
                    if verbose:
                        print(f"\n[claude][tokens] input={input_tokens} output={output_tokens}")  # noqa: T201
                    if langfuse:
                        for obs in tool_obs.values():
                            obs.update(output={"status": "completed"}).end()
                        tool_obs.clear()
                        langfuse.update_current_span(
                            input={"prompt": prompt[:200], **trace_meta},
                            output={"result": result_text[:500], "status": status},
                            metadata={
                                "session_id": session_id,
                                "status": status,
                                "input_tokens": input_tokens,
                                "output_tokens": output_tokens,
                                "backend": self.name,
                            },
                        )

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                await asyncio.wait_for(_run_query(), timeout=timeout)
                break
            except TimeoutError:
                if langfuse:
                    langfuse.update_current_span(metadata={"error": "timeout", "status": "timeout"})
                raise
            except Exception as exc:
                if attempt == max_attempts:
                    if langfuse:
                        langfuse.update_current_span(
                            metadata={"error": str(exc), "status": "exception"}
                        )
                    raise
                wait = 2**attempt
                if verbose:
                    print(f"[claude][retry {attempt}/{max_attempts - 1}] {exc} — retry in {wait}s")  # noqa: T201
                await asyncio.sleep(wait)

        return BackendResult(
            text=result_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            session_id=session_id,
            backend=self.name,
            tool_calls=tool_calls,
        )


def _summarise(d: dict) -> str:
    parts = []
    for k, v in list(d.items())[:3]:
        v_str = str(v)[:60].replace("\n", " ")
        parts.append(f"{k}={v_str!r}")
    return ", ".join(parts)
