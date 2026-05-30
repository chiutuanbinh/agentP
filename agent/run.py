#!/usr/bin/env python3
"""Agent entry point.

Usage:
    python run.py ENG-123
    python run.py ENG-123 --agent swe --repo /workspace/my-repo --verbose
    python run.py ENG-123 --agent pm --task "decompose epic into stories"
    python run.py ENG-123 --agent qa --pr 42
    python run.py ENG-123 --agent arch --pr 42
    python run.py --agent security --pr 42 --repo owner/repo

Available agents: swe (default), pm, qa, arch, security
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Allow `from agent.agents import ...` when run as `python agent/run.py`
sys.path.insert(0, str(Path(__file__).parent.parent))


def _check_env() -> list[str]:
    required = [
        "ANTHROPIC_API_KEY",
        "JIRA_URL",
        "JIRA_USER",
        "JIRA_API_TOKEN",
        "GITHUB_TOKEN",
    ]
    return [v for v in required if not os.environ.get(v)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent runner: ticket → action")
    parser.add_argument("ticket", nargs="?", help="Jira ticket key (e.g. ENG-123)")
    parser.add_argument(
        "--agent",
        "-a",
        default="swe",
        choices=["swe", "pm", "qa", "arch", "security"],
        help="Agent type (default: swe)",
    )
    parser.add_argument("--repo", help="Repo path (swe: existing checkout; security: owner/repo)")
    parser.add_argument("--pr", type=int, help="PR number (qa, arch, security)")
    parser.add_argument("--task", help="Task description (pm agent)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Stream agent output")
    args = parser.parse_args()

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    missing = _check_env()
    if missing:
        print(f"Missing required env vars: {', '.join(missing)}", file=sys.stderr)
        print("Set them in .env or export before running.", file=sys.stderr)
        sys.exit(1)

    result = asyncio.run(_dispatch(args))
    print("\n" + "=" * 60)
    print(result)


async def _dispatch(args) -> str:
    agent = args.agent

    if agent == "swe":
        from agent.agents.swe import run

        if not args.ticket:
            print("swe agent requires a ticket key", file=sys.stderr)
            sys.exit(1)
        print(f"Starting SWE agent for {args.ticket}...")
        return await run(args.ticket, repo_path=args.repo, verbose=args.verbose)

    if agent == "pm":
        from agent.agents.pm import run

        if not args.ticket:
            print("pm agent requires a ticket key", file=sys.stderr)
            sys.exit(1)
        task = args.task or "review and refine the ticket"
        print(f"Starting PM agent for {args.ticket} — {task}...")
        return await run(args.ticket, task=task, verbose=args.verbose)

    if agent == "qa":
        from agent.agents.qa import run

        if not args.ticket:
            print("qa agent requires a ticket key", file=sys.stderr)
            sys.exit(1)
        print(f"Starting QA agent for {args.ticket}...")
        return await run(args.ticket, pr_number=args.pr, verbose=args.verbose)

    if agent == "arch":
        from agent.agents.arch import run

        if not args.ticket:
            print("arch agent requires a ticket key", file=sys.stderr)
            sys.exit(1)
        print(f"Starting Architecture agent for {args.ticket}...")
        return await run(args.ticket, pr_number=args.pr, verbose=args.verbose)

    if agent == "security":
        from agent.agents.security import run

        print("Starting Security agent...")
        return await run(
            ticket_key=args.ticket,
            pr_number=args.pr,
            repo=args.repo,
            verbose=args.verbose,
        )

    print(f"Unknown agent: {agent}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
