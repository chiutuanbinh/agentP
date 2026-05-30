"""Backwards-compatibility shim — delegates to agents/swe.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.agents.swe import run  # noqa: F401, E402
