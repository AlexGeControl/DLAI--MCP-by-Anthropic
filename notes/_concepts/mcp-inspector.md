---
title: MCP Inspector
slug: mcp-inspector
tags: [concept]
---

# MCP Inspector

A standalone debugging **client** that lets you exercise an [[mcp-server]] by hand — list
its tools/resources/prompts and invoke them — before you've written any client code. It
stands in for a real [[mcp-client]] so you can verify a server in isolation.

```bash
npx @modelcontextprotocol/inspector uv run research_server.py
```

In the UI you set the launch command (`uv`, args `run research_server.py`), connect, then
click **List Tools** and **Run** a tool. Used in [[05-creating-an-mcp-server]] before the
real client of [[06-creating-an-mcp-client]] exists.

Related: [[mcp-server]] · [[mcp-client]] · [[stdio-transport]]
