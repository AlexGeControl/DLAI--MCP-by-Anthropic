---
tags: [concept]
related:
  - "[[03-mcp-architecture]]"
  - "[[06-creating-an-mcp-client]]"
  - "[[mcp-host]]"
  - "[[mcp-server]]"
  - "[[transport]]"
---

# mcp-client

The connector that lives **inside** a [[mcp-host]] and maintains a **1-to-1 connection**
to one [[mcp-server]]. A host with three servers runs three clients.

The client's job: **discover and invoke** what a server exposes — list/call [[tools]],
read [[resources]], fetch [[prompt-templates]] — by exchanging [[json-rpc]] messages over
a [[transport]]. The server *exposes*; the client *consumes*.

related: [[mcp-server]] · [[mcp-host]] · [[mcp-session-init]] · [[06-creating-an-mcp-client]] · [[mcp-architecture]]
