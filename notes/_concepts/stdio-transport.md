---
title: stdio transport
slug: stdio-transport
tags: [concept]
---

# stdio transport

The transport for **local** MCP: the [[mcp-client]] launches the [[mcp-server]] as a
**subprocess** and exchanges [[json-rpc]] messages over its standard input/output streams.
The client supplies the launch command (e.g. `uv run research_server.py`) and gets back a
`(read, write)` stream pair to drive a [[mcp-client]] session.

```python
mcp.run(transport="stdio")          # server side
async with stdio_client(params) as (read, write): ...   # client side
```

For remote servers the same server swaps to [[streamable-http-transport]] — usually a
one-line change.

Related: [[transport]] · [[streamable-http-transport]] · [[mcp-client]]
