---
title: FastMCP
slug: fastmcp
tags: [concept]
---

# FastMCP

The high-level Python class for building an [[mcp-server]] with minimal boilerplate. You
write plain functions and decorate them (`@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()`);
FastMCP handles the [[json-rpc]] protocol *and* **infers each tool's schema from its type
hints and docstring** — no hand-written JSON Schema (contrast [[04-chatbot-example]]).

```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("research")
mcp.run(transport="stdio")
```

The alternative is the low-level path: writing explicit `ListToolsRequest` /
`CallToolRequest` handlers for full control. Good type hints + docstrings *are* your API contract.

Related: [[mcp-server]] · [[tools]] · [[stdio-transport]]
