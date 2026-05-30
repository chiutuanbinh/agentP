"""Skill registry — import all skills from one place."""

from ._base import Skill
from .code_tools import CODE_TOOLS
from .confluence import CONFLUENCE
from .github import GITHUB
from .jira import JIRA
from .security_audit import SECURITY_AUDIT
from .testing import TESTING

__all__ = [
    "CODE_TOOLS",
    "CONFLUENCE",
    "GITHUB",
    "JIRA",
    "SECURITY_AUDIT",
    "TESTING",
    "Skill",
]
