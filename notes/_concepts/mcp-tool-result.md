---
title: MCP tool-call result (content vs structuredContent)
slug: mcp-tool-result
tags: [concept, mcp, tool-use]
---

# MCP tool-call result

What `await session.call_tool(...)` returns: an MCP **`CallToolResult`**. The
[[mcp-client]] translates this into an Anthropic `tool_result` block (see the
schema in [[anthropic-tool-use-schema]]) to continue the [[tool-use-loop]].

## The three fields

| field | type | always present? | purpose |
|---|---|---|---|
| `content` | list of typed blocks (`text`, `image`, `audio`, `resource`, `resource_link`) | ✅ yes | **unstructured, model-readable** representation — what you forward to the LLM |
| `structuredContent` | a single JSON object | only if the tool declares an `outputSchema` | **machine-readable**, schema-validated result — for *your code*, not the prompt |
| `isError` | `bool` | ✅ yes | `true` = the tool ran but **failed at the logic level** (bad args, not found). Distinct from a protocol/transport error, which *raises* instead |

## `content` vs `structuredContent` — which to use

Use **`content`** to build the LLM-facing `tool_result`. It's always present and
is the representation the model is meant to read.

`structuredContent` is the *typed mirror* — present only when the tool advertises
an `outputSchema`. Reach for it when **your program** needs the data (parse a
number, drive control flow, validate), not when feeding the model.

> The MCP spec says a tool returning `structuredContent` **SHOULD also emit a
> functionally-equivalent serialization in `content`** (usually the JSON as a
> `text` block), precisely so a client can forward *something* without
> understanding the schema. So `content` is the safe default; feeding **both** to
> the model is redundant.

Edge case: a tool that returns *only* `structuredContent` with no text mirror
leaves `content` empty — then `json.dumps(structuredContent)` into a text block is
a reasonable fallback (otherwise the client's `content or "(no text)"` guard kicks in).

## `isError` — let the model recover

A logic-level failure comes back as `isError: true` with the explanation inside
`content`. Pass it straight to the Anthropic `tool_result`'s `is_error` so Claude
sees the failure and adapts, rather than treating an error string as a real answer.
Transport/protocol failures don't set this — they raise, so wrap `call_tool` in
`try/except` and synthesize an `is_error` result yourself.

> [!tip] Phone takeaway
> `call_tool` → `CallToolResult{content, structuredContent, isError}`. Feed
> **`content`** to the LLM (always there, human/model-readable);
> **`structuredContent`** is the optional typed mirror for *your* code; propagate
> **`isError`** so Claude can recover.

Related: [[anthropic-tool-use-schema]] · [[tool-use-loop]] · [[tools]] · [[mcp-client]] · [[06-creating-an-mcp-client]]
