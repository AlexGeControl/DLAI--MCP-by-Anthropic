"""Integration tests for the FastMCP server.

Skipped entirely when ``mcp`` is not installed, so the offline unit suite still
passes in a vanilla environment.
"""

from __future__ import annotations

import pytest

pytest.importorskip("mcp")

from mcp_research import server  # noqa: E402


def test_server_instance_named_research():
    assert server.mcp.name == "research"


@pytest.mark.asyncio
async def test_tools_registered():
    tools = await server.mcp.list_tools()
    names = {t.name for t in tools}
    assert {"search_papers", "extract_info"} <= names


@pytest.mark.asyncio
async def test_prompt_registered():
    prompts = await server.mcp.list_prompts()
    names = {p.name for p in prompts}
    assert "generate_search_prompt" in names
