"""Skill registry — import all skills from one place."""

from ._base import Skill
from .agent_builder_docs import AGENT_BUILDER_DOCS
from .code_tools import CODE_TOOLS
from .confluence import CONFLUENCE
from .github import GITHUB
from .jira import JIRA
from .langfuse import LANGFUSE_SKILL
from .security_audit import SECURITY_AUDIT
from .slack import SLACK
from .testing import TESTING

__all__ = [
    "AGENT_BUILDER_DOCS",
    "CODE_TOOLS",
    "CONFLUENCE",
    "GITHUB",
    "JIRA",
    "LANGFUSE_SKILL",
    "SECURITY_AUDIT",
    "SLACK",
    "TESTING",
    "Skill",
]
