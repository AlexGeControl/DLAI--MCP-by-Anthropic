---
tags: [concept]
related:
  - "[[01-introduction]]"
  - "[[02-why-mcp]]"
  - "[[03-mcp-architecture]]"
  - "[[mcp-architecture]]"
---

# mcp

**Model Context Protocol** — an open, model-agnostic protocol that standardizes how
LLM applications connect to external **tools** and **data resources**. Launched by
Anthropic in November 2024.

The slogan: *models are only as good as the context provided to them.* MCP is the
"USB-C for AI" — one standard plug so you **build an integration once and reuse it
everywhere** (see [[02-why-mcp]]) instead of re-wiring every model to every data source.

It is to AI-context what REST is to web back ends, or what LSP is to editors — a shared
language layered over the existing idea of [[tools|tool use]], not a replacement for it.

related: [[mcp-architecture]] · [[mcp-server]] · [[mcp-client]] · [[mcp-host]]
