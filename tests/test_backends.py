"""Tests for agent/backends/ strategy layer."""

import asyncio
import contextlib
import sys
from io import StringIO
from typing import ClassVar
from unittest.mock import AsyncMock, MagicMock, patch

# ---------------------------------------------------------------------------
# Stub heavy SDK imports before any agent module is loaded.
# Use real dummy classes for types that backends check with isinstance().
# ---------------------------------------------------------------------------


# --- Claude SDK dummy types ---
class _SystemMessage:
    def __init__(self, subtype="", data=None):
        self.subtype = subtype
        self.data = data or {}


class _AssistantMessage:
    def __init__(self, content=()):
        self.content = list(content)


class _ResultMessage:
    def __init__(self, result="", subtype="success", usage=None):
        self.result = result
        self.subtype = subtype
        self.usage = usage or {}


class _TextBlock:
    def __init__(self, text=""):
        self.text = text


class _ToolUseBlock:
    def __init__(self, name="", input=None, id="tool-0"):
        self.name = name
        self.input = input or {}
        self.id = id


class _ClaudeAgentOptions:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


_claude_sdk_mock = MagicMock()
_claude_sdk_mock.SystemMessage = _SystemMessage
_claude_sdk_mock.AssistantMessage = _AssistantMessage
_claude_sdk_mock.ResultMessage = _ResultMessage
_claude_sdk_mock.TextBlock = _TextBlock
_claude_sdk_mock.ToolUseBlock = _ToolUseBlock
_claude_sdk_mock.ClaudeAgentOptions = _ClaudeAgentOptions
sys.modules.setdefault("claude_agent_sdk", _claude_sdk_mock)
sys.modules.setdefault("langfuse", MagicMock())


# --- Copilot SDK dummy types ---
class _AssistantMessageData:
    def __init__(self, content=""):
        self.content = content


class _SessionIdleData:
    pass


_copilot_events_mock = MagicMock()
_copilot_events_mock.AssistantMessageData = _AssistantMessageData
_copilot_events_mock.SessionIdleData = _SessionIdleData

sys.modules.setdefault("copilot", MagicMock())
sys.modules.setdefault("copilot.generated", MagicMock())
sys.modules["copilot.generated.session_events"] = _copilot_events_mock
sys.modules.setdefault("copilot.session", MagicMock())
sys.modules.setdefault("copilot.tools", MagicMock())


from agent.agents._base import BaseAgent  # noqa: E402
from agent.backends._base import BackendResult, LLMBackend  # noqa: E402
from agent.backends.claude import ClaudeBackend  # noqa: E402
from agent.backends.copilot import CopilotBackend  # noqa: E402
from agent.skills._base import Skill  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SKILL_X = Skill(name="x", tools=("Bash", "Read"), prompt_section="## X\nUse X.")
SKILL_Y = Skill(name="y", tools=("Read", "Write"), prompt_section="## Y\nUse Y.")


class _TestAgent(BaseAgent):
    AGENT_NAME = "test_agent"
    SKILLS: ClassVar[list[Skill]] = [SKILL_X, SKILL_Y]


def _run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# BackendResult
# ---------------------------------------------------------------------------


class TestBackendResult:
    def test_required_field(self):
        r = BackendResult(text="hello")
        assert r.text == "hello"

    def test_defaults(self):
        r = BackendResult(text="x")
        assert r.input_tokens == 0
        assert r.output_tokens == 0
        assert r.session_id is None
        assert r.backend == ""
        assert r.tool_calls == []

    def test_tool_calls_not_shared(self):
        a = BackendResult(text="a")
        b = BackendResult(text="b")
        a.tool_calls.append("Bash")
        assert b.tool_calls == []

    def test_all_fields(self):
        r = BackendResult(
            text="out",
            input_tokens=10,
            output_tokens=5,
            session_id="s-1",
            backend="claude",
            tool_calls=["Read"],
        )
        assert r.input_tokens == 10
        assert r.session_id == "s-1"
        assert r.tool_calls == ["Read"]


# ---------------------------------------------------------------------------
# LLMBackend ABC
# ---------------------------------------------------------------------------


class TestLLMBackendABC:
    def test_cannot_instantiate_directly(self):
        try:
            LLMBackend()
            raise AssertionError("Expected TypeError")
        except TypeError:
            pass

    def test_concrete_subclass_must_implement_run(self):
        class _Incomplete(LLMBackend):
            name = "incomplete"

        try:
            _Incomplete()
            raise AssertionError("Expected TypeError")
        except TypeError:
            pass

    def test_concrete_subclass_ok(self):
        class _OK(LLMBackend):
            name = "ok"

            async def run(self, **kwargs):
                return BackendResult(text="done")

        assert _OK().name == "ok"


# ---------------------------------------------------------------------------
# ClaudeBackend
# ---------------------------------------------------------------------------


def _make_claude_messages(result_text="done", tool_names=(), error=False):
    """Build a fake async generator yielding Claude SDK message types."""

    async def _gen():
        init = _SystemMessage(subtype="init", data={"session_id": "sess-abc"})
        yield init

        if tool_names:
            blocks = []
            for i, name in enumerate(tool_names):
                tb = _ToolUseBlock(name=name, input={"path": "/workspace/f"}, id=f"tool-{i}")
                blocks.append(tb)
            blocks.append(_TextBlock(text="thinking..."))
            yield _AssistantMessage(content=blocks)

        yield _ResultMessage(
            result=result_text,
            subtype="error" if error else "success",
            usage={"input_tokens": 10, "output_tokens": 5},
        )

    return _gen()


class TestClaudeBackend:
    def _call(self, messages=None, verbose=False, timeout=30.0, model=None):
        if messages is None:
            messages = _make_claude_messages("result text")

        with patch("agent.backends.claude.query", return_value=messages):
            return _run(
                ClaudeBackend().run(
                    prompt="do the thing",
                    system_prompt="You are an agent.",
                    allowed_tools=["Bash"],
                    model=model,
                    cwd="/workspace",
                    verbose=verbose,
                    timeout=timeout,
                    langfuse=None,
                    trace_meta={},
                    mcp_servers={},
                )
            )

    def test_returns_backend_result(self):
        r = self._call()
        assert isinstance(r, BackendResult)

    def test_result_text_extracted(self):
        r = self._call(_make_claude_messages("my result"))
        assert r.text == "my result"

    def test_backend_name(self):
        r = self._call()
        assert r.backend == "claude"

    def test_session_id_captured(self):
        r = self._call()
        assert r.session_id == "sess-abc"

    def test_token_counts(self):
        r = self._call()
        assert r.input_tokens == 10
        assert r.output_tokens == 5

    def test_tool_calls_recorded(self):
        msgs = _make_claude_messages(tool_names=["Read", "Write"])
        r = self._call(msgs)
        assert r.tool_calls == ["Read", "Write"]

    def test_verbose_prints(self):
        msgs = _make_claude_messages("out", tool_names=["Bash"])
        captured = StringIO()
        with patch("sys.stdout", captured):
            self._call(msgs, verbose=True)
        output = captured.getvalue()
        assert "sess-abc" in output
        assert "Bash" in output

    def test_query_called_with_correct_options(self):
        from claude_agent_sdk import ClaudeAgentOptions

        msgs = _make_claude_messages()
        with patch("agent.backends.claude.query", return_value=msgs) as mock_q:
            _run(
                ClaudeBackend().run(
                    prompt="p",
                    system_prompt="sys",
                    allowed_tools=["Read"],
                    model="claude-opus-4-8",
                    cwd="/workspace",
                    verbose=False,
                    timeout=60.0,
                    langfuse=None,
                    trace_meta={},
                    mcp_servers={"srv": {}},
                )
            )
        args, kwargs = mock_q.call_args
        opts = kwargs.get("options") or args[1]
        assert isinstance(opts, ClaudeAgentOptions)
        assert opts.model == "claude-opus-4-8"
        assert "Read" in opts.allowed_tools

    def test_retry_on_transient_error(self):
        call_count = 0

        async def _flaky(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("transient")
            async for m in _make_claude_messages("recovered"):
                yield m

        with patch("agent.backends.claude.query", side_effect=_flaky):
            r = _run(
                ClaudeBackend().run(
                    prompt="p",
                    system_prompt="s",
                    allowed_tools=[],
                    model=None,
                    cwd="/workspace",
                    verbose=False,
                    timeout=30.0,
                    langfuse=None,
                    trace_meta={},
                    mcp_servers={},
                )
            )
        assert r.text == "recovered"
        assert call_count == 3

    def test_exhausted_retries_raises(self):
        with patch("agent.backends.claude.query", side_effect=RuntimeError("boom")):
            try:
                _run(
                    ClaudeBackend().run(
                        prompt="p",
                        system_prompt="s",
                        allowed_tools=[],
                        model=None,
                        cwd="/workspace",
                        verbose=False,
                        timeout=30.0,
                        langfuse=None,
                        trace_meta={},
                        mcp_servers={},
                    )
                )
                raise AssertionError("Expected RuntimeError")
            except RuntimeError as e:
                assert "boom" in str(e)

    def test_langfuse_span_updated_on_success(self):
        lf = MagicMock()
        msgs = _make_claude_messages("ok", tool_names=["Bash"])
        with patch("agent.backends.claude.query", return_value=msgs):
            _run(
                ClaudeBackend().run(
                    prompt="p",
                    system_prompt="s",
                    allowed_tools=[],
                    model=None,
                    cwd="/workspace",
                    verbose=False,
                    timeout=30.0,
                    langfuse=lf,
                    trace_meta={"task": "t1"},
                    mcp_servers={},
                )
            )
        lf.update_current_span.assert_called()
        call_kwargs = lf.update_current_span.call_args_list[-1][1]
        assert call_kwargs["output"]["status"] == "success"


# ---------------------------------------------------------------------------
# CopilotBackend
# ---------------------------------------------------------------------------


def _make_copilot_session(response_text="copilot result", tool_names=()):
    """Return a mock (client, session) pair for CopilotBackend tests.

    Uses the dummy _AssistantMessageData / _SessionIdleData classes so that
    isinstance checks inside CopilotBackend._run() succeed.
    """

    def _make_event(data):
        e = MagicMock()
        e.data = data
        return e

    captured_handler = []

    async def _send(message):
        # Fire pre_tool_use hook for each tool name
        hooks = captured_hooks[0] if captured_hooks else {}
        for name in tool_names:
            pre_hook = hooks.get("on_pre_tool_use")
            if pre_hook:
                inp = {"toolName": name}
                await pre_hook(inp, {})

        msg_event = _make_event(_AssistantMessageData(content=response_text))
        for h in captured_handler:
            h(msg_event)

        idle_event = _make_event(_SessionIdleData())
        for h in captured_handler:
            h(idle_event)

    captured_hooks: list[dict] = []

    session = MagicMock()
    session.send = AsyncMock(side_effect=_send)
    session.on = lambda h: captured_handler.append(h)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)

    async def _create_session(**kwargs):
        captured_hooks.append(kwargs.get("hooks", {}))
        return session

    client = MagicMock()
    client.create_session = AsyncMock(side_effect=_create_session)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    return client, session


class TestCopilotBackend:
    def _call(self, response_text="copilot done", tool_names=(), verbose=False, model=None):
        client, _session = _make_copilot_session(response_text, tool_names)

        with patch("copilot.CopilotClient", return_value=client):
            return _run(
                CopilotBackend().run(
                    prompt="do it",
                    system_prompt="You are a copilot agent.",
                    allowed_tools=["Bash"],  # should be ignored
                    model=model,
                    cwd="/workspace",
                    verbose=verbose,
                    timeout=30.0,
                    langfuse=None,
                    trace_meta={},
                    mcp_servers={},
                )
            )

    def test_returns_backend_result(self):
        r = self._call()
        assert isinstance(r, BackendResult)

    def test_backend_name(self):
        r = self._call()
        assert r.backend == "copilot"

    def test_result_text(self):
        r = self._call(response_text="copilot answer")
        assert "copilot answer" in r.text

    def test_no_session_id(self):
        r = self._call()
        assert r.session_id is None

    def test_model_default(self):
        client, _ = _make_copilot_session()
        with patch("copilot.CopilotClient", return_value=client):
            _run(
                CopilotBackend().run(
                    prompt="p",
                    system_prompt="s",
                    allowed_tools=[],
                    model=None,
                    cwd="/workspace",
                    verbose=False,
                    timeout=30.0,
                    langfuse=None,
                    trace_meta={},
                    mcp_servers={},
                )
            )
        _, kwargs = client.create_session.call_args
        assert kwargs.get("model") == "gpt-4o"

    def test_model_override(self):
        client, _ = _make_copilot_session()
        with patch("copilot.CopilotClient", return_value=client):
            _run(
                CopilotBackend().run(
                    prompt="p",
                    system_prompt="s",
                    allowed_tools=[],
                    model="claude-sonnet-4-5",
                    cwd="/workspace",
                    verbose=False,
                    timeout=30.0,
                    langfuse=None,
                    trace_meta={},
                    mcp_servers={},
                )
            )
        _, kwargs = client.create_session.call_args
        assert kwargs["model"] == "claude-sonnet-4-5"

    def test_system_prompt_passed_as_system_message(self):
        client, _ = _make_copilot_session()
        with patch("copilot.CopilotClient", return_value=client):
            _run(
                CopilotBackend().run(
                    prompt="p",
                    system_prompt="Be a pirate.",
                    allowed_tools=[],
                    model=None,
                    cwd="/workspace",
                    verbose=False,
                    timeout=30.0,
                    langfuse=None,
                    trace_meta={},
                    mcp_servers={},
                )
            )
        _, kwargs = client.create_session.call_args
        assert kwargs["system_message"]["text"] == "Be a pirate."

    def test_cwd_passed_to_client(self):
        client, _ = _make_copilot_session()
        with patch("copilot.CopilotClient", return_value=client) as mock_cls:
            _run(
                CopilotBackend().run(
                    prompt="p",
                    system_prompt="s",
                    allowed_tools=[],
                    model=None,
                    cwd="/my/workspace",
                    verbose=False,
                    timeout=30.0,
                    langfuse=None,
                    trace_meta={},
                    mcp_servers={},
                )
            )
            _, kwargs = mock_cls.call_args
            assert kwargs.get("working_directory") == "/my/workspace"
            client.create_session.assert_called_once()

    def test_verbose_prints(self):
        captured = StringIO()
        with patch("sys.stdout", captured):
            self._call(verbose=True)
        output = captured.getvalue()
        assert len(output) > 0

    def test_github_token_from_env(self):
        client, _ = _make_copilot_session()
        with (
            patch("copilot.CopilotClient", return_value=client) as mock_cls,
            patch.dict("os.environ", {"GITHUB_TOKEN": "ghp_test123"}),
        ):
            _run(
                CopilotBackend().run(
                    prompt="p",
                    system_prompt="s",
                    allowed_tools=[],
                    model=None,
                    cwd="/workspace",
                    verbose=False,
                    timeout=30.0,
                    langfuse=None,
                    trace_meta={},
                    mcp_servers={},
                )
            )
        _, kwargs = mock_cls.call_args
        assert kwargs.get("github_token") == "ghp_test123"

    def test_langfuse_span_updated(self):
        lf = MagicMock()
        client, _ = _make_copilot_session("result")
        with patch("copilot.CopilotClient", return_value=client):
            _run(
                CopilotBackend().run(
                    prompt="p",
                    system_prompt="s",
                    allowed_tools=[],
                    model=None,
                    cwd="/workspace",
                    verbose=False,
                    timeout=30.0,
                    langfuse=lf,
                    trace_meta={"task": "t1"},
                    mcp_servers={},
                )
            )
        lf.update_current_span.assert_called()


# ---------------------------------------------------------------------------
# BaseAgent strategy dispatch
# ---------------------------------------------------------------------------


class TestBaseAgentStrategy:
    def test_default_backend_is_claude(self):
        assert BaseAgent.BACKEND is ClaudeBackend

    def test_agent_inherits_claude_backend(self):
        assert _TestAgent.BACKEND is ClaudeBackend

    def test_override_backend_at_class_level(self):
        class _CopilotAgent(_TestAgent):
            BACKEND = CopilotBackend

        assert _CopilotAgent.BACKEND is CopilotBackend

    def test_run_uses_class_backend(self):
        mock_backend = MagicMock(spec=LLMBackend)
        mock_backend.name = "mock"
        mock_backend.run = AsyncMock(return_value=BackendResult(text="from mock"))

        class _MockBackendClass:
            name = "mock"

            def __new__(cls):
                return mock_backend

        class _Agent(_TestAgent):
            BACKEND = _MockBackendClass

        with patch.object(_Agent, "_base_prompt", return_value="BASE"):
            result = _run(_Agent.run("test prompt"))

        assert result == "from mock"
        mock_backend.run.assert_called_once()

    def test_run_kwarg_overrides_class_backend(self):
        mock_backend = MagicMock(spec=LLMBackend)
        mock_backend.name = "override"
        mock_backend.run = AsyncMock(return_value=BackendResult(text="kwarg backend"))

        class _KwargBackend:
            name = "override"

            def __new__(cls):
                return mock_backend

        with patch.object(_TestAgent, "_base_prompt", return_value="BASE"):
            result = _run(_TestAgent.run("p", backend=_KwargBackend))

        assert result == "kwarg backend"

    def test_run_passes_system_prompt_to_backend(self):
        mock_backend = MagicMock(spec=LLMBackend)
        mock_backend.name = "m"
        mock_backend.run = AsyncMock(return_value=BackendResult(text="ok"))

        class _MB:
            def __new__(cls):
                return mock_backend

        with patch.object(_TestAgent, "_base_prompt", return_value="MY SYSTEM PROMPT"):
            _run(_TestAgent.run("p", backend=_MB))

        _, kwargs = mock_backend.run.call_args
        assert "MY SYSTEM PROMPT" in kwargs["system_prompt"]

    def test_run_passes_allowed_tools_to_backend(self):
        mock_backend = MagicMock(spec=LLMBackend)
        mock_backend.name = "m"
        mock_backend.run = AsyncMock(return_value=BackendResult(text="ok"))

        class _MB:
            def __new__(cls):
                return mock_backend

        with patch.object(_TestAgent, "_base_prompt", return_value="BASE"):
            _run(_TestAgent.run("p", backend=_MB))

        _, kwargs = mock_backend.run.call_args
        assert "Bash" in kwargs["allowed_tools"]
        assert "Read" in kwargs["allowed_tools"]
        assert "Write" in kwargs["allowed_tools"]
        # deduped
        assert kwargs["allowed_tools"].count("Read") == 1

    def test_run_passes_mcp_servers_to_backend(self):
        mock_backend = MagicMock(spec=LLMBackend)
        mock_backend.name = "m"
        mock_backend.run = AsyncMock(return_value=BackendResult(text="ok"))

        class _MB:
            def __new__(cls):
                return mock_backend

        class _AgentWithMCP(_TestAgent):
            MCP_SERVERS: ClassVar[dict] = {"my-mcp": {"type": "stdio", "command": "uv"}}

        with patch.object(_AgentWithMCP, "_base_prompt", return_value="BASE"):
            _run(_AgentWithMCP.run("p", backend=_MB))

        _, kwargs = mock_backend.run.call_args
        assert "my-mcp" in kwargs["mcp_servers"]

    def test_dry_run_never_calls_backend(self):
        mock_backend = MagicMock(spec=LLMBackend)
        mock_backend.run = AsyncMock(return_value=BackendResult(text="should not happen"))

        class _MB:
            def __new__(cls):
                return mock_backend

        with patch.object(_TestAgent, "_base_prompt", return_value="BASE"):
            result = _run(_TestAgent.run("p", dry_run=True, backend=_MB))

        assert result == ""
        mock_backend.run.assert_not_called()

    def test_langfuse_flushed_even_on_error(self):
        lf = MagicMock()
        lf.start_as_current_observation.return_value.__enter__ = MagicMock(return_value=lf)
        lf.start_as_current_observation.return_value.__exit__ = MagicMock(return_value=False)

        mock_backend = MagicMock(spec=LLMBackend)
        mock_backend.name = "m"
        mock_backend.run = AsyncMock(side_effect=RuntimeError("backend died"))

        class _MB:
            def __new__(cls):
                return mock_backend

        with (
            patch.object(_TestAgent, "_base_prompt", return_value="BASE"),
            patch.object(_TestAgent, "_make_langfuse", return_value=lf),
            contextlib.suppress(RuntimeError),
        ):
            _run(_TestAgent.run("p", backend=_MB))

        lf.flush.assert_called_once()
