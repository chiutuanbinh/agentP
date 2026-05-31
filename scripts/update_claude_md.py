"""Regenerate the Architecture section of CLAUDE.md from current codebase state.

Inspects agent/agents/, agent/backends/, agent/skills/, mcp_*.py, scripts/
and rewrites the ## Architecture block in-place. All other sections preserved.

Usage:
    uv run scripts/update_claude_md.py [--dry-run] [--check]

Exit codes: 0=no change (or dry-run), 1=updated (pre-push hook uses this to decide commit)
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
CLAUDE_MD = REPO / "CLAUDE.md"

# ──────────────────────────────────────────────────────────────────────────────
# Scanners
# ──────────────────────────────────────────────────────────────────────────────


def _module_docstring(path: Path) -> str:
    """Return first line of module docstring, or empty string."""
    try:
        tree = ast.parse(path.read_text())
        doc = ast.get_docstring(tree)
        if doc:
            return doc.splitlines()[0].rstrip(".")
    except SyntaxError:
        pass
    return ""


def _agent_name(path: Path) -> str | None:
    """Extract AGENT_NAME string constant from an agent file."""
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for t in item.targets:
                        if isinstance(t, ast.Name) and t.id == "AGENT_NAME":
                            try:
                                return ast.literal_eval(item.value)
                            except ValueError, TypeError:
                                pass
    return None


def _backend_name(path: Path) -> str | None:
    """Extract name = '...' from a backend class."""
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for t in item.targets:
                        if isinstance(t, ast.Name) and t.id == "name":
                            try:
                                return ast.literal_eval(item.value)
                            except ValueError, TypeError:
                                pass
    return None


def _mcp_server_name(path: Path) -> str | None:
    """Extract FastMCP("name") from an MCP server file."""
    try:
        src = path.read_text()
        m = re.search(r'FastMCP\(\s*["\']([^"\']+)["\']', src)
        if m:
            return m.group(1)
    except OSError:
        pass
    return None


def _skill_name(path: Path) -> str | None:
    """Extract Skill(name='...') from a skill file."""
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            if name == "Skill":
                for kw in node.keywords:
                    if kw.arg == "name":
                        try:
                            return ast.literal_eval(kw.value)
                        except ValueError, TypeError:
                            pass
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Section builder
# ──────────────────────────────────────────────────────────────────────────────


def build_architecture_section() -> str:
    lines: list[str] = ["## Architecture", ""]

    # ── Dynamic: top-level experiment directories ────────────────────────────
    top_level_dirs = [d for d in ["adk", "claude", "agent"] if (REPO / d).is_dir()]
    n = len(top_level_dirs)
    lines.append(f"{n} experiment director{'y' if n == 1 else 'ies'}:")
    lines.append("")

    if (REPO / "adk").is_dir():
        lines += [
            "**`adk/`** — Google ADK agent (`google-adk`). Entry: `root_agent` in `adk/agent.py`."
            " Run via `adk web`. Session state in `adk/.adk/session.db` (gitignored).",
            "",
        ]

    if (REPO / "claude").is_dir():
        claude_files = sorted((REPO / "claude").glob("*.py"))
        lines.append("**`claude/`** — Anthropic Claude experiments:")
        for f in claude_files:
            doc = _module_docstring(f)
            entry = f"- `{f.name}`"
            if doc:
                entry += f" — {doc}"
            lines.append(entry)
        lines.append("")

    # ── agent/ system ────────────────────────────────────────────────────────
    lines += [
        "**`agent/`** — Multi-agent system: ticket → PR workflow using Claude Agent SDK.",
        "- `run.py` — CLI entry; validates env, loads `.env`, dispatches to agent type"
        f" (`--agent {_agent_types()}`)",
        "- `agents/_base.py` — `BaseAgent`: template method for prompt assembly, tool union,"
        " Langfuse tracing, backend dispatch",
        "- `agents/{...}.py` — one class + `run()` per agent type (see below)",
        f"- `backends/{{...}}.py` — LLMBackend strategy layer: {_backend_list()}",
        "- `skills/{...}.py` — composable skill units (tools + prompt section)",
        "- `prompts/{...}.md` — system prompts, one per agent",
        "- `jira_client.py` — Jira REST API CLI; agent invokes via `Bash`:"
        " `python jira_client.py get|search|comment|transition <args>`",
        "- `wiki_client.py` — Confluence REST API CLI; agent invokes via `Bash`:"
        " `python wiki_client.py search|get|get-by-title <args>`",
        "",
    ]

    # ── Agents ───────────────────────────────────────────────────────────────
    lines.append("**Agents** (`agent/agents/`):")
    for path in sorted((REPO / "agent" / "agents").glob("*.py")):
        if path.stem.startswith("_"):
            continue
        name = _agent_name(path) or path.stem
        doc = _module_docstring(path)
        entry = f"- `{path.stem}.py` (`{name}`)"
        if doc:
            entry += f" — {doc}"
        lines.append(entry)
    lines.append("")

    # ── Backends ─────────────────────────────────────────────────────────────
    lines.append("**Backends** (`agent/backends/`) — LLMBackend strategy:")
    for path in sorted((REPO / "agent" / "backends").glob("*.py")):
        if path.stem.startswith("_"):
            continue
        bname = _backend_name(path)
        doc = _module_docstring(path)
        entry = f"- `{path.stem}.py`"
        if bname:
            entry += f' (`name="{bname}"`)'
        if doc:
            entry += f" — {doc}"
        lines.append(entry)
    lines.append("")

    # ── Skills ───────────────────────────────────────────────────────────────
    lines.append("**Skills** (`agent/skills/`) — composable tool + prompt units:")
    for path in sorted((REPO / "agent" / "skills").glob("*.py")):
        if path.stem.startswith("_"):
            continue
        sname = _skill_name(path)
        doc = _module_docstring(path)
        entry = f"- `{path.stem}.py`"
        if sname:
            entry += f" (`{sname}`)"
        if doc:
            entry += f" — {doc}"
        lines.append(entry)
    lines.append("")

    # ── MCP servers ──────────────────────────────────────────────────────────
    mcp_files = sorted(REPO.glob("mcp_*.py"))
    if mcp_files:
        lines.append("**MCP servers** (root):")
        for path in mcp_files:
            sname = _mcp_server_name(path) or path.stem
            doc = _module_docstring(path)
            entry = f"- `{path.name}` (`{sname}`)"
            if doc:
                entry += f" — {doc}"
            lines.append(entry)
        lines.append("")

    # ── Scripts ──────────────────────────────────────────────────────────────
    script_files = sorted((REPO / "scripts").glob("*.py"))
    if script_files:
        lines.append("**Scripts** (`scripts/`):")
        for path in script_files:
            doc = _module_docstring(path)
            entry = f"- `{path.name}`"
            if doc:
                entry += f" — {doc}"
            lines.append(entry)
        lines.append("")

    return "\n".join(lines)


def _agent_types() -> str:
    names = []
    for path in sorted((REPO / "agent" / "agents").glob("*.py")):
        if path.stem.startswith("_"):
            continue
        name = _agent_name(path)
        if name:
            names.append(name)
    return "|".join(names) if names else "..."


def _backend_list() -> str:
    names = []
    for path in sorted((REPO / "agent" / "backends").glob("*.py")):
        if path.stem.startswith("_"):
            continue
        n = _backend_name(path)
        if n:
            names.append(f"`{n}`")
    return ", ".join(names) if names else "..."


# ──────────────────────────────────────────────────────────────────────────────
# CLAUDE.md patcher
# ──────────────────────────────────────────────────────────────────────────────

# Match ## Architecture through (but not including) the next ## section or end-of-file.
_ARCH_RE = re.compile(r"## Architecture\n.*?(?=\n## |\Z)", re.DOTALL)


def patch_claude_md(current: str, new_section: str) -> str:
    """Replace ALL ## Architecture blocks with a single updated one."""
    new_block = new_section.rstrip("\n")
    if not _ARCH_RE.search(current):
        return current.rstrip("\n") + "\n\n" + new_block + "\n"

    count = [0]

    def _replace_once(m: re.Match) -> str:
        count[0] += 1
        return new_block if count[0] == 1 else ""

    return _ARCH_RE.sub(_replace_once, current)


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print new section, don't write")
    parser.add_argument("--check", action="store_true", help="Exit 1 if CLAUDE.md would change")
    args = parser.parse_args()

    new_section = build_architecture_section()

    if args.dry_run:
        print(new_section)
        return 0

    current = CLAUDE_MD.read_text()
    updated = patch_claude_md(current, new_section)

    if updated == current:
        print("CLAUDE.md up to date.")
        return 0

    if args.check:
        print("CLAUDE.md would be updated (run without --check to apply).")
        return 1

    CLAUDE_MD.write_text(updated)
    print("CLAUDE.md updated.")
    return 1  # signal to hook: file changed, please commit


if __name__ == "__main__":
    sys.exit(main())
