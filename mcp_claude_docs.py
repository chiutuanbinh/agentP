"""MCP server for fetching live Claude SDK documentation."""

import httpx
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("claude-sdk-docs")

BASE_URL = "https://code.claude.com/docs/en/agent-sdk"
DOCS_INDEX = {
    "agent-loop": f"{BASE_URL}/agent-loop",
    "overview": f"{BASE_URL}/overview",
    "tools": f"{BASE_URL}/tools",
    "computer-use": f"{BASE_URL}/computer-use",
}


def _fetch_doc(url: str) -> str:
    with httpx.Client(follow_redirects=True, timeout=15) as client:
        resp = client.get(url)
        resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    # strip nav/header/footer noise
    for tag in soup(["nav", "header", "footer", "script", "style"]):
        tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.body
    return (
        main.get_text(separator="\n", strip=True)
        if main
        else soup.get_text(separator="\n", strip=True)
    )


@mcp.tool()
def get_agent_sdk_doc(page: str = "agent-loop") -> str:
    """Fetch live Claude Agent SDK documentation page.

    Args:
        page: Doc page slug. Options: agent-loop, overview, tools, computer-use.
             Defaults to agent-loop.
    """
    url = DOCS_INDEX.get(page, f"{BASE_URL}/{page}")
    return _fetch_doc(url)


@mcp.tool()
def get_doc_by_url(url: str) -> str:
    """Fetch any Claude docs page by full URL.

    Args:
        url: Full URL to fetch.
    """
    return _fetch_doc(url)


@mcp.tool()
def list_doc_pages() -> dict:
    """List known Claude Agent SDK doc pages."""
    return DOCS_INDEX


if __name__ == "__main__":
    mcp.run()
