"""Quick harness to test agent/ agents without the full run.py CLI."""

import asyncio
import logging
import sys
from pathlib import Path

# Make agent/ importable as a package
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from agent.agents.agent_builder import AgentBuilderAgent
from agent.agents.arch import ArchAgent
from agent.agents.pm import PMAgent
from agent.agents.qa import QAAgent
from agent.agents.security import SecurityAgent
from agent.agents.swe import SWEAgent

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

AGENTS = {
    "swe": SWEAgent,
    "pm": PMAgent,
    "qa": QAAgent,
    "arch": ArchAgent,
    "security": SecurityAgent,
    "agent_builder": AgentBuilderAgent,
}


async def main():
    agent_name = sys.argv[1] if len(sys.argv) > 1 else "swe"
    prompt = sys.argv[2] if len(sys.argv) > 2 else None

    agent_cls = AGENTS.get(agent_name)
    if agent_cls is None:
        log.error("Unknown agent '%s'. Choose from: %s", agent_name, ", ".join(AGENTS))
        sys.exit(1)

    if prompt is None:
        log.info("=== %s system prompt ===\n%s", agent_name, agent_cls.system_prompt())
        log.info("=== allowed tools ===\n%s", agent_cls.allowed_tools())
        return

    result = await agent_cls.run(prompt, verbose=True)
    log.info("=== result ===\n%s", result)


asyncio.run(main())
