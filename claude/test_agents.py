"""Quick harness to test agent/ agents without the full run.py CLI."""

import asyncio
import sys
from pathlib import Path

# Make agent/ importable as a package
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.agents.agent_builder import AgentBuilderAgent
from agent.agents.arch import ArchAgent
from agent.agents.pm import PMAgent
from agent.agents.qa import QAAgent
from agent.agents.security import SecurityAgent
from agent.agents.swe import SWEAgent

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
        sys.stdout.write(f"Unknown agent '{agent_name}'. Choose from: {', '.join(AGENTS)}\n")
        sys.exit(1)

    if prompt is None:
        sys.stdout.write(f"=== {agent_name} system prompt ===\n\n")
        sys.stdout.write(agent_cls.system_prompt() + "\n")
        sys.stdout.write(f"\n=== allowed tools ===\n{agent_cls.allowed_tools()}\n")
        return

    result = await agent_cls.run(prompt, verbose=True)
    sys.stdout.write(f"\n=== result ===\n{result}\n")


asyncio.run(main())
