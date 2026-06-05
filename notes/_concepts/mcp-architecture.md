---
tags: [concept]
related:
  - "[[03-mcp-architecture]]"
  - "[[mcp]]"
  - "[[mcp-host]]"
  - "[[mcp-client]]"
  - "[[mcp-server]]"
  - "[[transport]]"
  - "[[json-rpc]]"
---

# mcp-architecture

The **client–server** shape of [[mcp]]. A [[mcp-host]] (the LLM app, e.g. Claude Desktop)
holds one or more [[mcp-client]]s; each client keeps a **1-to-1 connection** to one
[[mcp-server]]. Servers expose three **primitives**: [[tools]], [[resources]], and
[[prompt-templates]].

Messages flow over a [[transport]] (stdio locally; HTTP-based remotely) and are encoded
as [[json-rpc]] requests, responses, and notifications, framed by an initialize →
exchange → terminate lifecycle.

related: [[03-mcp-architecture]] · [[mcp-host]] · [[mcp-client]] · [[mcp-server]] · [[transport]]
