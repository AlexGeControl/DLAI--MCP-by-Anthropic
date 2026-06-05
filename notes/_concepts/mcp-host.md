---
tags: [concept]
related:
  - "[[03-mcp-architecture]]"
  - "[[mcp-client]]"
  - "[[mcp-server]]"
  - "[[mcp]]"
---

# mcp-host

The **LLM application** that wants to access data through [[mcp]] — e.g. Claude Desktop,
Claude AI, Cursor, or your own chatbot. The host **owns and maintains** all the
[[mcp-client]]s and their connections to [[mcp-server]]s.

The host also owns the *human-in-the-loop* UX: whether to ask the user before a tool runs
is the host's interface choice, not the server's.

related: [[mcp-client]] · [[mcp-architecture]] · [[03-mcp-architecture]]
