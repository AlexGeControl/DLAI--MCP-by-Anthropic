#!/usr/bin/env python3
"""Smoke-test that a FastMCP server module registers its primitives, WITHOUT
launching a blocking transport.

This is the fast "does it even wire up?" check before opening the Inspector.
It imports the given module, grabs its module-level ``mcp`` (a FastMCP), and
lists the registered tools / resources / resource-templates / prompts.

Usage:
    python scripts/smoke_server.py <module.path.with.mcp>
    python scripts/smoke_server.py            # defaults to mcp_research.server
"""
from __future__ import annotations

import importlib
import sys

import anyio  # ships with `mcp`


def main() -> int:
    modpath = sys.argv[1] if len(sys.argv) > 1 else "mcp_research.server"
    try:
        module = importlib.import_module(modpath)
    except Exception as exc:  # noqa: BLE001 - surface any import-time error clearly
        print(f"FAILED to import {modpath!r}: {exc}")
        return 2
    mcp = getattr(module, "mcp", None)
    if mcp is None:
        print(f"{modpath!r} has no module-level `mcp` (FastMCP) object")
        return 2

    async def run() -> int:
        tools = await mcp.list_tools()
        resources = await mcp.list_resources()
        templates = await mcp.list_resource_templates()
        prompts = await mcp.list_prompts()
        print(f"server   : {getattr(mcp, 'name', modpath)}")
        print("tools    :", [t.name for t in tools])
        print("resources:", [str(r.uri) for r in resources])
        print("templates:", [r.uriTemplate for r in templates])
        print("prompts  :", [p.name for p in prompts])
        if not (tools or resources or templates or prompts):
            print("WARNING: server registered nothing")
            return 1
        return 0

    return anyio.run(run)


if __name__ == "__main__":
    sys.exit(main())
