---
tags: [concept]
related:
  - "[[03-mcp-architecture]]"
  - "[[05-creating-an-mcp-server]]"
  - "[[mcp-client]]"
  - "[[tools]]"
  - "[[resources]]"
  - "[[prompt-templates]]"
---

# mcp-server

A **lightweight program** that exposes specific capabilities to a [[mcp-client]] over a
[[transport]]. The three things it can expose: [[tools]], [[resources]], and
[[prompt-templates]].

Think of it as a **gateway/wrapper around an API** — instead of calling the API directly,
the host talks to it in natural language and the server handles execution. Servers are
**reusable across any MCP-compatible app**; anyone can write one, and many are published
as community reference servers.

related: [[mcp-client]] · [[05-creating-an-mcp-server]] · [[tools]] · [[resources]] · [[prompt-templates]]
