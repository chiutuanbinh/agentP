#!/usr/bin/env python3
"""SWE agent entry point.

Usage:
    python run.py ENG-123
    python run.py ENG-123 --repo /workspace/my-repo --verbose
"""

import argparse
import asyncio
import os
import sys


def _check_env() -> list[str]:
    required = ["ANTHROPIC_API_KEY", "JIRA_URL", "JIRA_USER", "JIRA_API_TOKEN", "GITHUB_TOKEN"]
    missing = [v for v in required if not os.environ.get(v)]
    return missing


def main() -> None:
    parser = argparse.ArgumentParser(description="SWE agent: ticket → PR")
    parser.add_argument("ticket", help="Jira ticket key (e.g. ENG-123)")
    parser.add_argument("--repo", help="Path to existing local repo checkout", default=None)
    parser.add_argument("--verbose", "-v", action="store_true", help="Stream agent output")
    args = parser.parse_args()

    # Load .env before env check
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

    from swe_agent import run

    print(f"Starting SWE agent for {args.ticket}...")
    result = asyncio.run(run(args.ticket, repo_path=args.repo, verbose=args.verbose))
    print("\n" + "=" * 60)
    print(result)


if __name__ == "__main__":
    main()
