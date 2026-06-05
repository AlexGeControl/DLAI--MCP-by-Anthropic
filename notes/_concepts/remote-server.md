---
tags: [concept]
aliases: [remote-mcp-server, deployed-server]
---

# remote-server

**An MCP server reachable over the network by URL** rather than spawned locally.
The server code is essentially unchanged from the local version — only the
[[transport]] swaps from [[stdio-transport]] to [[streamable-http-transport]]
(and a host/port is set).

Deploying means: containerize or push the repo (the course uses Docker / Render),
expose the HTTP endpoint, and connect clients via a URL. Remote servers add
concerns local ones lack — notably **authentication** (OAuth 2.1, see
[[11-conclusion]]) instead of stdio's environment variables.

Related: [[mcp-server]] · [[streamable-http-transport]] · [[10-creating-and-deploying-remote-servers]]
