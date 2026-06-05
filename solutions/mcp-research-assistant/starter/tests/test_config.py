"""Offline unit tests for config loading. No third-party deps required."""

from __future__ import annotations

import json

import pytest

from mcp_research.config import load_server_config

SAMPLE = {
    "mcpServers": {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
        },
        "research": {"command": "uv", "args": ["run", "research_server.py"]},
        "fetch": {"command": "uvx", "args": ["mcp-server-fetch"]},
    }
}


def _write(tmp_path, obj) -> str:
    path = tmp_path / "server_config.json"
    path.write_text(json.dumps(obj), encoding="utf-8")
    return str(path)


def test_load_valid_config(tmp_path):
    cfg = load_server_config(_write(tmp_path, SAMPLE))
    assert set(cfg["mcpServers"]) == {"filesystem", "research", "fetch"}
    assert cfg["mcpServers"]["research"]["command"] == "uv"


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_server_config(str(tmp_path / "nope.json"))


def test_invalid_json_raises(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError):
        load_server_config(str(path))


def test_missing_mcpservers_defaults_to_empty(tmp_path):
    cfg = load_server_config(_write(tmp_path, {"other": 1}))
    assert cfg["mcpServers"] == {}


def test_non_object_root_raises(tmp_path):
    cfg_path = _write(tmp_path, [1, 2, 3])
    with pytest.raises(ValueError):
        load_server_config(cfg_path)


def test_non_object_mcpservers_raises(tmp_path):
    cfg_path = _write(tmp_path, {"mcpServers": [1, 2]})
    with pytest.raises(ValueError):
        load_server_config(cfg_path)
