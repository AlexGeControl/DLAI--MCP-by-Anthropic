---
title: Anthropic tool-use message schema
slug: anthropic-tool-use-schema
tags: [concept, anthropic, tool-use]
---

# Anthropic tool-use message schema

The concrete wire shapes the Anthropic **Messages API** uses to drive the
[[tool-use-loop]]. Knowing these is what makes `process_query` in
[[06-creating-an-mcp-client]] work; getting them subtly wrong is what the
[[openai-to-anthropic-migration]] traps are about.

## Request side — `messages.create(...)`

- **`system`**
  - The system prompt is a **top-level string parameter**, *not* a
  `{"role": "system"}` entry in `messages`. 
  - `messages` roles are only `user` / `assistant`.
- **`tools`**
  - Should be a list of `{"name", "description", "input_schema"}`, in which `input_schema` is raw JSON Schema.
  - Tool **names must match `^[a-zA-Z0-9_-]{1,128}$`** — no `@`, `/`, or `.`, so namespacing a server's tools needs a safe delimiter like `__`.
- **`tool_choice`** — an *internally-tagged object*, never a bare string:
  - `{"type": "auto"}` (default with tools)
  - `{"type": "any"}` (must call one)
  - `{"type": "tool", "name": ...}` (force one)
  - `{"type": "none"}` (no tool call).

## Response side — the `Message` object

### `message.content` Explained

`message.content` is a **list of typed blocks** — branch on `block.type`:

| block type | key fields | meaning |
|---|---|---|
| `text` | `.text` | prose to show the user |
| `tool_use` | `.id`, `.name`, `.input` | the model wants a tool run |
| `thinking` | `.thinking` | reasoning (only if thinking enabled) |

### `message.stop_reason` Explained

`message.stop_reason` says *why it stopped*: 
- `tool_use` (run tools, loop again),
- `end_turn` (done)
- plus `max_tokens`, `refusal`, `pause_turn`. 
**Treat anything that isn't `tool_use` as terminal** — looping on an unhandled reason spins forever.

## Feeding results back

1. Append the assistant turn **verbatim**: `{"role": "assistant", "content": message.content}` — the `tool_use` blocks must survive into history. Otherwise the server side status could be corrupted.
2. Append a **`user`** turn whose content is a list of `tool_result` blocks:
   ```python
   {"type": "tool_result",
    "tool_use_id": block.id,       # must match the tool_use it answers
    "content": [...] or "fallback",# str, or list of text/image blocks
    "is_error": bool}              # True lets Claude recover from failures
   ```
3. **Every `tool_use` in a turn needs a matching `tool_result`** in the next user turn, or the following call 400s.

### The `tool_result` block schema

| field | type | required | notes |
|---|---|---|---|
| `type` | `"tool_result"` | ✅ | the block discriminator |
| `tool_use_id` | `str` | ✅ | **must equal** the `.id` of the `tool_use` it answers — this is what pairs request↔result |
| `content` | `str` **or** list of content blocks | ✅ | the result payload. A plain string, or a list of `{"type":"text","text":…}` / `{"type":"image",…}` blocks. **An empty list `[]` is rejected** — always supply a fallback string |
| `is_error` | `bool` | — (default `false`) | `true` marks a *failed* call; Claude reads the content as an error and can retry or apologize instead of trusting garbage |

The `tool_result` blocks all live in **one** `user` turn (one block per `tool_use`),
appended after the assistant turn that requested them.

### Bridging from an MCP tool result

When the tool lives behind an [[mcp-server]], you don't build `content` by hand —
you **translate** the server's `CallToolResult` into this block: 
- Map its `content` text/image items into Anthropic content blocks, 
- And pass its `isError` straight through to `is_error`. 

The shape of that MCP-side result — and why you read `content` rather than `structuredContent` — is its own atom: **[[mcp-tool-result]]**.

> [!tip] Phone takeaway
> Tools/`tool_choice`/`system` go in the **request**; the model answers with a
> `content` list of `text`/`tool_use` blocks + a `stop_reason`; you reply with a
> `user` turn of `tool_result` blocks keyed by `tool_use_id`. Loop while
> `stop_reason == "tool_use"`.

Related: [[tool-use-loop]] · [[openai-to-anthropic-migration]] · [[tools]] · [[mcp-tool-result]] · [[06-creating-an-mcp-client]]
