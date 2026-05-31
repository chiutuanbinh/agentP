"""Sync agent/ Python definitions → .claude/agents/*.md

Source of truth: agent/agents/*.py + agent/prompts/*.md + agent/skills/

Run:
    uv run scripts/sync_agents.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.agents.agent_builder import AgentBuilderAgent  # noqa: E402
from agent.agents.arch import ArchAgent  # noqa: E402
from agent.agents.pm import PMAgent  # noqa: E402
from agent.agents.qa import QAAgent  # noqa: E402
from agent.agents.security import SecurityAgent  # noqa: E402
from agent.agents.swe import SWEAgent  # noqa: E402

AGENTS = [
    (
        "swe",
        SWEAgent,
        (
            "Senior software engineer agent. Implements Jira tickets end-to-end:"
            " fetch context, write code, test, open PR."
            " Use when given a Jira ticket key to implement."
        ),
    ),
    (
        "pm",
        PMAgent,
        (
            "Product manager agent. Manages Jira tickets, writes specs, decomposes epics."
            " Use when decomposing a large ticket or writing acceptance criteria."
        ),
    ),
    (
        "qa",
        QAAgent,
        (
            "QA engineer agent. Reviews PRs for test coverage, writes test plans,"
            " creates bug tickets."
            " Use when reviewing a PR or writing a test plan for a ticket."
        ),
    ),
    (
        "arch",
        ArchAgent,
        (
            "Software architect agent. Reviews designs, writes ADRs,"
            " identifies systemic code issues."
            " Use when reviewing architecture of a PR or writing an ADR."
        ),
    ),
    (
        "security",
        SecurityAgent,
        (
            "Security engineer agent. Audits code and PRs for vulnerabilities,"
            " writes findings, creates remediation tickets."
            " Use when doing a security review of a PR or codebase."
        ),
    ),
    (
        "agent_builder",
        AgentBuilderAgent,
        (
            "Agent builder. Creates new agents using Claude Agent SDK and Langfuse docs."
            " Use when asked to build a new agent in this codebase."
        ),
    ),
]

OUT_DIR = REPO_ROOT / ".claude" / "agents"


def render(name: str, cls, description: str) -> str:
    tools = cls.allowed_tools()
    tools_yaml = "[" + ", ".join(tools) + "]"
    system_prompt = cls.system_prompt()
    lines = [
        "---",
        f"name: {name}",
        f"description: {description}",
        f"tools: {tools_yaml}",
        "---",
        "",
        system_prompt,
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Sync agent definitions to .claude/agents/")
    parser.add_argument("--dry-run", action="store_true", help="Print output, don't write files")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for name, cls, description in AGENTS:
        content = render(name, cls, description)
        out_path = OUT_DIR / f"{name}.md"

        if args.dry_run:
            sys.stdout.write(f"=== {out_path} ===\n{content[:300]}\n...\n\n")
        else:
            out_path.write_text(content)
            sys.stdout.write(f"wrote {out_path.relative_to(REPO_ROOT)}\n")


if __name__ == "__main__":
    main()
