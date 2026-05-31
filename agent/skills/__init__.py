"""Skill registry — import all skills from one place."""

from ._base import Skill
from .agent_builder_docs import AGENT_BUILDER_DOCS
from .azure_data import AZURE_DATA
from .code_tools import CODE_TOOLS
from .confluence import CONFLUENCE
from .copilot import COPILOT_SKILL
from .databricks import DATABRICKS
from .github import GITHUB
from .jira import JIRA
from .langfuse import LANGFUSE_SKILL
from .postgres import POSTGRES
from .security_audit import SECURITY_AUDIT
from .slack import SLACK
from .telegram import TELEGRAM
from .testing import TESTING

__all__ = [
    "AGENT_BUILDER_DOCS",
    "AZURE_DATA",
    "CODE_TOOLS",
    "CONFLUENCE",
    "COPILOT_SKILL",
    "DATABRICKS",
    "GITHUB",
    "JIRA",
    "LANGFUSE_SKILL",
    "POSTGRES",
    "SECURITY_AUDIT",
    "SLACK",
    "TELEGRAM",
    "TESTING",
    "Skill",
]
