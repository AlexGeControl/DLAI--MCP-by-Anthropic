"""Loading and validating the MCP server configuration.

The config file mirrors the Claude Desktop / ``mcp`` convention: a JSON document
with a top-level ``mcpServers`` mapping of ``name -> {command, args, ...}``.
"""

from __future__ import annotations

import json
import os
from typing import Any


def load_server_config(path: str = "server_config.json") -> dict[str, Any]:
    """Load and minimally validate an MCP server configuration file.

    Args:
        path: Path to the JSON config file.

    Returns:
        The parsed config as a dict. Guaranteed to contain an ``"mcpServers"``
        key mapping to a dict (possibly empty).

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        ValueError: If the file is not valid JSON, the top level is not an
            object, or ``mcpServers`` is present but not an object.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Server config not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a JSON object, got {type(data).__name__}")

    servers = data.get("mcpServers", {})
    if not isinstance(servers, dict):
        raise ValueError("'mcpServers' must be a JSON object")

    data["mcpServers"] = servers
    return data
