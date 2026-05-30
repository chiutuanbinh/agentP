"""Agent registry — maps agent name to module."""

from .arch import ArchAgent
from .pm import PMAgent
from .qa import QAAgent
from .security import SecurityAgent
from .swe import SWEAgent

REGISTRY: dict[str, type] = {
    "swe": SWEAgent,
    "pm": PMAgent,
    "qa": QAAgent,
    "arch": ArchAgent,
    "security": SecurityAgent,
}

__all__ = [
    "REGISTRY",
    "ArchAgent",
    "PMAgent",
    "QAAgent",
    "SWEAgent",
    "SecurityAgent",
]
