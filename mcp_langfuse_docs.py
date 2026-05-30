"""MCP server for Langfuse documentation and local OpenAPI spec."""

import httpx
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("langfuse-docs")

LANGFUSE_LOCAL = "http://localhost:3000"
DOCS_BASE = "https://langfuse.com/docs"

DOCS_INDEX = {
    # Core SDK / tracing
    "python-sdk": f"{DOCS_BASE}/sdk/python",
    "tracing": f"{DOCS_BASE}/tracing",
    "tracing-data-model": f"{DOCS_BASE}/tracing/data-model",
    "observations": f"{DOCS_BASE}/tracing/observations",
    "sessions": f"{DOCS_BASE}/tracing/sessions",
    "scores": f"{DOCS_BASE}/scores",
    # SDK upgrade guides
    "python-v3-to-v4": f"{DOCS_BASE}/sdk/python/upgrade-path/python-v3-to-v4",
    # Integrations
    "claude-agent-sdk": "https://langfuse.com/integrations/claude-agent-sdk",
    "openai": "https://langfuse.com/integrations/openai-py",
    # Prompt management
    "prompts": f"{DOCS_BASE}/prompts/get-started",
    # Self-hosting
    "docker-compose": "https://langfuse.com/self-hosting/docker-compose",
    # API reference
    "api-reference": "https://langfuse.com/docs/public-api",
}


def _fetch_text(url: str) -> str:
    with httpx.Client(follow_redirects=True, timeout=20) as client:
        resp = client.get(url)
        resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["nav", "header", "footer", "script", "style"]):
        tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.body
    return (
        main.get_text(separator="\n", strip=True)
        if main
        else soup.get_text(separator="\n", strip=True)
    )


@mcp.tool()
def list_langfuse_doc_pages() -> dict:
    """List known Langfuse documentation page slugs and their URLs."""
    return DOCS_INDEX


@mcp.tool()
def get_langfuse_doc(page: str = "python-sdk") -> str:
    """Fetch a Langfuse documentation page by slug.

    Args:
        page: Slug from list_langfuse_doc_pages(). Defaults to python-sdk.
    """
    url = DOCS_INDEX.get(page, f"{DOCS_BASE}/{page}")
    return _fetch_text(url)


@mcp.tool()
def get_langfuse_doc_by_url(url: str) -> str:
    """Fetch any Langfuse documentation URL.

    Args:
        url: Full URL of the page to fetch.
    """
    return _fetch_text(url)


@mcp.tool()
def get_langfuse_llms_index() -> str:
    """Fetch the full Langfuse llms.txt index listing all documentation pages."""
    with httpx.Client(follow_redirects=True, timeout=20) as client:
        resp = client.get("https://langfuse.com/llms.txt")
        resp.raise_for_status()
    return resp.text


@mcp.tool()
def get_langfuse_openapi_spec() -> dict:
    """Fetch the OpenAPI spec from the local Langfuse instance at localhost:3000.

    Returns the raw OpenAPI JSON if available, or an error dict.
    """
    candidates = [
        f"{LANGFUSE_LOCAL}/api/public/openapi.json",
        f"{LANGFUSE_LOCAL}/api/openapi.json",
        f"{LANGFUSE_LOCAL}/openapi.json",
    ]
    with httpx.Client(follow_redirects=True, timeout=10) as client:
        for url in candidates:
            try:
                resp = client.get(url)
                if resp.status_code == 200 and "application/json" in resp.headers.get(
                    "content-type", ""
                ):
                    return resp.json()
            except Exception:  # noqa: S112
                continue
    # Fall back to public API spec from GitHub
    try:
        with httpx.Client(follow_redirects=True, timeout=20) as client:
            resp = client.get(
                "https://raw.githubusercontent.com/langfuse/langfuse/main/packages/shared/src/server/routers/fern.yaml"
            )
            if resp.status_code == 200:
                return {"source": "github-fern-yaml", "content": resp.text[:8000]}
    except Exception:  # noqa: S110
        pass
    return {"error": "OpenAPI spec not found locally or remotely", "tried": candidates}


if __name__ == "__main__":
    mcp.run()
