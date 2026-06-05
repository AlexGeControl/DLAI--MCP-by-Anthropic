---
title: Tools
slug: tools
tags: [concept]
---

# Tools

Functions the model can ask to invoke to extend its abilities beyond text — search a
database, hit an API, write a file — instead of saying "I don't know" or hallucinating.
Each tool carries a **name**, a **description**, and an **input schema** (JSON Schema of
its parameters); the model reads these to decide *when* and *how* to call it.

- In a plain app the schema is **hand-written JSON** ([[04-chatbot-example]]).
- Behind a [[mcp-server]], [[fastmcp]] *infers* the schema from type hints + docstrings.
- One of MCP's three primitives, alongside [[resources]] and [[prompt-templates]].

Related: [[tool-use-loop]] · [[mcp-server]] · [[fastmcp]]
