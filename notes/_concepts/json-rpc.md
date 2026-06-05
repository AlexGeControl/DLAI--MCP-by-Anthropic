---
tags: [concept]
related:
  - "[[03-mcp-architecture]]"
  - "[[transport]]"
  - "[[mcp-architecture]]"
---

# json-rpc

The **message format** [[mcp]] speaks. Communication is a set of JSON-RPC **requests**,
**responses**, and **notifications** exchanged between [[mcp-client]] and [[mcp-server]]
over a [[transport]].

The connection follows a lifecycle: **initialize** (request → response → `initialized`
notification) → **message exchange** (either side may send requests/notifications) →
**terminate**. This is why the SDK code surfaces methods like `initialize`.

related: [[transport]] · [[mcp-architecture]] · [[03-mcp-architecture]]
