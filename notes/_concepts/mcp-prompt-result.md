---
title: MCP prompt get result
slug: mcp-prompt-result
tags: [concept, mcp, prompts]
---

# MCP prompt get result

What `await session.get_prompt(name, arguments)` returns: a **`GetPromptResult`**.
The prompt counterpart of [[mcp-resource-result]] / [[mcp-tool-result]] — but the
payload is **ready-to-send conversation messages**, not data or a tool's output.

## The schema

`GetPromptResult` = `meta`, `description`, and **`messages`** — a list of
`PromptMessage`:

| field | type | notes |
|---|---|---|
| `description` | `str` | human summary of the rendered prompt |
| `messages` | `list[PromptMessage]` | the rendered conversation to run |

`PromptMessage` = **`role`** (`"user"` / `"assistant"` — the same vocabulary as the
Anthropic Messages API) + **`content`** — note **one block, not a list** (contrast
the resource `contents` *list* and the `tool_result` content *list*). The block is
one of:

| content type | payload | use |
|---|---|---|
| `TextContent` | `.text` | the common case — the rendered instruction text |
| `ImageContent` / `AudioContent` | `.data` (base64) + `.mimeType` | host maps to a provider block, as in [[mcp-resource-result]] |
| `EmbeddedResource` | `.resource` (a `Text`/`BlobResourceContents`) | resource bytes baked into the prompt — the "resource → model" path |
| `ResourceLink` | `.uri` (+ `name`/`mimeType`) | a *pointer* to a resource, not its bytes |

## Consuming it

`role` already matches Anthropic's vocabulary, so conversion is mostly pulling text:

```python
result = await session.get_prompt(name, arguments)
anthropic_messages = [
    {"role": m.role, "content": m.content.text}       # TextContent — the usual case
    for m in result.messages
    if m.content.type == "text"
]
```

In this project's flow the prompt renders to a single user message: extract
`result.messages[0].content.text` and hand it to `process_query` to run — see
[[mcp-prompt-access]].

## vs. tool / resource results

| | [[mcp-tool-result]] | [[mcp-resource-result]] | prompt get (`GetPromptResult`) |
|---|---|---|---|
| trigger | model (`tool_use`) | app / user | app / user (slash command) |
| payload | `content` blocks (+ `structuredContent`) | `contents` (text/blob parts) | **`messages`** (role + one block each) |
| meant to | answer a tool call | supply context **data** | **drive a conversation turn** |
| error | `isError` flag | raises | raises |

The defining difference: a prompt result is **conversation to *run***, whereas a
resource result is **data to *inject***.

> [!tip] Phone takeaway
> `get_prompt` → `GetPromptResult.messages`: a list of `PromptMessage` =
> `role` (user/assistant) + **one** `content` block (usually `TextContent.text`).
> It's a **conversation to run**, not data to inject; `role` already matches
> Anthropic's. No `isError` — failures raise.

Related: [[mcp-prompt-access]] · [[prompt-templates]] · [[mcp-resource-result]] · [[mcp-tool-result]] · [[mcp-session-init]] · [[08-adding-prompt-and-resource-features]]
