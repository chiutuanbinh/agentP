#!/usr/bin/env python3
"""Jira REST API CLI — called by the SWE agent via Bash."""

import json
import os
import sys

import requests
from requests.auth import HTTPBasicAuth


def _auth() -> HTTPBasicAuth:
    user = os.environ["JIRA_USER"]
    token = os.environ["JIRA_API_TOKEN"]
    return HTTPBasicAuth(user, token)


def _base() -> str:
    return os.environ["JIRA_URL"].rstrip("/")


def get_ticket(key: str) -> dict:
    url = f"{_base()}/rest/api/3/issue/{key}"
    r = requests.get(url, auth=_auth(), timeout=15)
    r.raise_for_status()
    data = r.json()
    fields = data["fields"]
    return {
        "key": data["key"],
        "summary": fields.get("summary", ""),
        "description": _adf_to_text(fields.get("description")),
        "status": fields.get("status", {}).get("name", ""),
        "priority": fields.get("priority", {}).get("name", ""),
        "assignee": (fields.get("assignee") or {}).get("displayName", "unassigned"),
        "reporter": (fields.get("reporter") or {}).get("displayName", ""),
        "labels": fields.get("labels", []),
        "components": [c["name"] for c in fields.get("components", [])],
        "fix_versions": [v["name"] for v in fields.get("fixVersions", [])],
        "issue_type": fields.get("issuetype", {}).get("name", ""),
        "acceptance_criteria": _get_custom_field(fields, "Acceptance Criteria"),
        "repo": _get_custom_field(fields, "GitHub Repo"),
        "branch": _get_custom_field(fields, "Target Branch"),
        "related_docs": _get_custom_field(fields, "Documentation Link"),
    }


def search_tickets(jql: str, max_results: int = 20) -> list[dict]:
    url = f"{_base()}/rest/api/3/issue/search"
    params = {
        "jql": jql,
        "maxResults": max_results,
        "fields": "summary,status,priority,assignee",
    }
    r = requests.get(url, auth=_auth(), params=params, timeout=15)
    r.raise_for_status()
    issues = r.json().get("issues", [])
    return [
        {
            "key": i["key"],
            "summary": i["fields"].get("summary", ""),
            "status": i["fields"].get("status", {}).get("name", ""),
        }
        for i in issues
    ]


def add_comment(key: str, body: str) -> None:
    url = f"{_base()}/rest/api/3/issue/{key}/comment"
    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": body}]}
            ],
        }
    }
    r = requests.post(url, auth=_auth(), json=payload, timeout=15)
    r.raise_for_status()


def transition_ticket(key: str, status_name: str) -> None:
    url = f"{_base()}/rest/api/3/issue/{key}/transitions"
    r = requests.get(url, auth=_auth(), timeout=15)
    r.raise_for_status()
    transitions = r.json().get("transitions", [])
    match = next(
        (t for t in transitions if status_name.lower() in t["name"].lower()), None
    )
    if not match:
        available = [t["name"] for t in transitions]
        raise ValueError(
            f"Transition '{status_name}' not found. Available: {available}"
        )
    r2 = requests.post(
        url, auth=_auth(), json={"transition": {"id": match["id"]}}, timeout=15
    )
    r2.raise_for_status()


def _adf_to_text(node: dict | None) -> str:
    if not node:
        return ""
    if node.get("type") == "text":
        return node.get("text", "")
    parts = [_adf_to_text(child) for child in node.get("content", [])]
    separator = (
        "\n"
        if node.get("type")
        in ("paragraph", "heading", "listItem", "bulletList", "orderedList")
        else ""
    )
    return separator.join(filter(None, parts))


def _get_custom_field(fields: dict, name: str) -> str:
    for key, val in fields.items():
        if isinstance(val, dict) and val.get("name") == name:
            return str(val.get("value", ""))
        if (
            key.startswith("customfield_")
            and isinstance(val, str)
            and name.lower() in key.lower()
        ):
            return val
    return ""


COMMANDS = {
    "get": lambda args: get_ticket(args[0]),
    "search": lambda args: search_tickets(
        args[0], int(args[1]) if len(args) > 1 else 20
    ),
    "comment": lambda args: (add_comment(args[0], args[1]), "ok")[1],
    "transition": lambda args: (transition_ticket(args[0], args[1]), "ok")[1],
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: jira_client.py <command> [args...]")
        print(
            "Commands: get <KEY> | search <JQL> [max] | comment <KEY> <text> | transition <KEY> <status>"
        )
        sys.exit(1)
    cmd = sys.argv[1]
    handler = COMMANDS.get(cmd)
    if not handler:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)
    result = handler(sys.argv[2:])
    print(json.dumps(result, indent=2, default=str))
