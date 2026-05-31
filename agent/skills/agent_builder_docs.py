"""Agent builder docs skill — MCP tools for Claude Agent SDK and Langfuse docs."""

from ._base import Skill

AGENT_BUILDER_DOCS = Skill(
    name="agent_builder_docs",
    tools=(
        # Claude Agent SDK docs
        "mcp__claude-sdk-docs__get_agent_sdk_doc",
        "mcp__claude-sdk-docs__get_doc_by_url",
        "mcp__claude-sdk-docs__list_doc_pages",
        # Langfuse docs (local MCP)
        "mcp__langfuse-docs__get_langfuse_doc",
        "mcp__langfuse-docs__get_langfuse_doc_by_url",
        "mcp__langfuse-docs__get_langfuse_llms_index",
        "mcp__langfuse-docs__get_langfuse_openapi_spec",
        "mcp__langfuse-docs__list_langfuse_doc_pages",
        # Langfuse docs (official remote MCP)
        "mcp__langfuse-official__getLangfuseDocsPage",
        "mcp__langfuse-official__getLangfuseOverview",
        "mcp__langfuse-official__searchLangfuseDocs",
    ),
    prompt_section="""\
## Agent Builder Docs
- Use `mcp__claude-sdk-docs__list_doc_pages` to discover available Claude Agent SDK docs
- Use `mcp__claude-sdk-docs__get_agent_sdk_doc` to read SDK reference pages before writing
  agent code
- Use `mcp__langfuse-docs__list_langfuse_doc_pages` to discover Langfuse tracing docs
- Use `mcp__langfuse-docs__get_langfuse_doc` or `mcp__langfuse-official__searchLangfuseDocs`
  for Langfuse integration patterns
- Always consult SDK docs before choosing tool names, option fields, or message types
- Never guess SDK APIs — look them up first
""",
)
