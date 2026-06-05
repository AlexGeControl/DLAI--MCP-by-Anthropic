"""mcp_research: an arXiv research MCP server + a modernized MCP chatbot client."""

from __future__ import annotations

__version__ = "0.1.0"

from . import arxiv_tools, config

__all__ = ["arxiv_tools", "config", "__version__"]
