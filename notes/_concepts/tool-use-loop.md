---
title: Tool-use loop
slug: tool-use-loop
tags: [concept]
---

# Tool-use loop

The agentic cycle an LLM app runs so the model can act, not just talk: send a query
**plus tool schemas** → if the reply contains a `tool_use` block, the app executes that
tool itself and appends the result as a `tool_result` message → call the model again →
repeat until the reply is plain text. The model decides *which* tool and *with what args*;
the **app** does the actual calling and feeds results back.

- Same loop whether tools are local Python functions ([[04-chatbot-example]]) or remote
  [[mcp-server]] tools ([[06-creating-an-mcp-client]]) — only *how the result is fetched* changes.
- Built on the Anthropic Messages API `tools=` parameter and `tool_use`/`tool_result` content.
- The exact request/response shapes (and how to feed results back) live in
  [[anthropic-tool-use-schema]]; SDK-specific pitfalls in [[openai-to-anthropic-migration]].

Related: [[tools]] · [[mcp-client]] · [[json-rpc]] · [[anthropic-tool-use-schema]]
