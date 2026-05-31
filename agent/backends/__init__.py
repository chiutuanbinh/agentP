"""LLM backend strategies for agent execution."""

from ._base import BackendResult, LLMBackend
from .claude import ClaudeBackend
from .copilot import CopilotBackend

__all__ = ["BackendResult", "ClaudeBackend", "CopilotBackend", "LLMBackend"]
