#!/usr/bin/env python3
"""Confluence wiki CLI — called by the SWE agent via Bash."""

import json
import os
import sys

import requests
from requests.auth import HTTPBasicAuth


def _auth() -> HTTPBasicAuth:
    user = os.environ.get("CONFLUENCE_USER") or os.environ["JIRA_USER"]
    token = os.environ.get("CONFLUENCE_API_TOKEN") or os.environ["JIRA_API_TOKEN"]
    return HTTPBasicAuth(user, token)


def _base() -> str:
    url = os.environ.get("CONFLUENCE_URL") or os.environ["JIRA_URL"]
    return url.rstrip("/")


def search(query: str, space: str = "", max_results: int = 10) -> list[dict]:
    url = f"{_base()}/rest/api/content/search"
    cql = f'type=page AND text~"{query}"'
    if space:
        cql += f' AND space.key="{space}"'
    params = {"cql": cql, "limit": max_results, "expand": "space,version"}
    r = requests.get(url, auth=_auth(), params=params, timeout=20)
    r.raise_for_status()
    results = r.json().get("results", [])
    return [
        {
            "id": p["id"],
            "title": p["title"],
            "space": p.get("space", {}).get("key", ""),
            "url": f"{_base()}/wiki{p['_links']['webui']}",
        }
        for p in results
    ]


def get_page(page_id: str) -> dict:
    url = f"{_base()}/rest/api/content/{page_id}"
    params = {"expand": "body.storage,version,space,ancestors"}
    r = requests.get(url, auth=_auth(), params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    html = data.get("body", {}).get("storage", {}).get("value", "")
    return {
        "id": data["id"],
        "title": data["title"],
        "space": data.get("space", {}).get("key", ""),
        "url": f"{_base()}/wiki{data['_links']['webui']}",
        "content": _html_to_text(html),
        "version": data.get("version", {}).get("number", 0),
    }


def get_page_by_title(space: str, title: str) -> dict:
    url = f"{_base()}/rest/api/content"
    params = {"spaceKey": space, "title": title, "expand": "body.storage,version"}
    r = requests.get(url, auth=_auth(), params=params, timeout=20)
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results:
        raise ValueError(f"Page '{title}' not found in space '{space}'")
    data = results[0]
    html = data.get("body", {}).get("storage", {}).get("value", "")
    return {
        "id": data["id"],
        "title": data["title"],
        "space": space,
        "url": f"{_base()}/wiki{data['_links']['webui']}",
        "content": _html_to_text(html),
    }


def _html_to_text(html: str) -> str:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    except ImportError:
        import re
        return re.sub(r"<[^>]+>", "", html)


COMMANDS = {
    "search": lambda args: search(args[0], args[1] if len(args) > 1 else "", int(args[2]) if len(args) > 2 else 10),
    "get": lambda args: get_page(args[0]),
    "get-by-title": lambda args: get_page_by_title(args[0], args[1]),
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: wiki_client.py <command> [args...]")
        print("Commands: search <query> [space] [max] | get <page_id> | get-by-title <space> <title>")
        sys.exit(1)
    cmd = sys.argv[1]
    handler = COMMANDS.get(cmd)
    if not handler:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)
    result = handler(sys.argv[2:])
    print(json.dumps(result, indent=2, default=str))
