---
tags: [concept]
related:
  - "[[03-mcp-architecture]]"
  - "[[stdio-transport]]"
  - "[[streamable-http-transport]]"
  - "[[json-rpc]]"
  - "[[mcp-architecture]]"
---

# transport

The layer that handles the **mechanics of moving messages** between an [[mcp-client]] and
an [[mcp-server]]. You pick a transport based on *how* you run the app; the [[json-rpc]]
message content is the same either way.

- **[[stdio-transport]]** — local: the client launches the server as a subprocess and they
  read/write over stdin/stdout.
- **[[streamable-http-transport]]** — remote: HTTP GET/POST to an endpoint, with an
  optional server-sent-events upgrade. Supports both stateful and stateless deployments;
  it is the recommended remote transport going forward (older standalone **SSE** is
  deprecated).

related: [[stdio-transport]] · [[streamable-http-transport]] · [[mcp-architecture]]
