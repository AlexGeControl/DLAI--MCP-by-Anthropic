---
tags: [concept]
aliases: [streamable-http, http-transport, sse-transport]
---

# streamable-http-transport

**The transport for remote MCP servers** — the server runs as an HTTP service
clients reach over a URL, instead of being spawned as a local subprocess
([[stdio-transport]]). Switching is nearly a one-line change to `mcp.run(...)`.

> [!warning] Staleness
> The course records `transport='sse'` (standalone Server-Sent Events).
> SSE was **deprecated as a standalone transport** in MCP spec `2025-03-26`;
> use **`transport='streamable-http'`** today. SSE survives only as an optional
> streaming channel *inside* Streamable HTTP.

Related: [[transport]] · [[stdio-transport]] · [[remote-server]] · [[10-creating-and-deploying-remote-servers]]
