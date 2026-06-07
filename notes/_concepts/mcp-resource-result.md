---
title: MCP resource read result
slug: mcp-resource-result
tags: [concept, mcp, resources]
---

# MCP resource read result

What `await session.read_resource(uri)` returns: a **`ReadResourceResult`**. The
resource counterpart of [[mcp-tool-result]] — but simpler, because reading a
resource is a plain **data fetch**, not a model-invoked action.

## The schema

`ReadResourceResult` has only `meta` and **`contents`** — a **list** (one URI can
return multiple parts) of either `TextResourceContents` or `BlobResourceContents`:

| part type | fields | payload | use for |
|---|---|---|---|
| `TextResourceContents` | `uri`, `mimeType`, **`text`** | UTF-8 string | text / markdown / json — inject into context directly |
| `BlobResourceContents` | `uri`, `mimeType`, **`blob`** | base64 string | binary (image, pdf) — `base64.b64decode` first |

Both share `uri` + `mimeType` (+ `meta`); they differ only by `.text` vs `.blob`.
Branch on the type (or on which attribute is present):

```python
import base64, mcp.types as types

result = await session.read_resource(uri)
for part in result.contents:                       # always a list
    if isinstance(part, types.TextResourceContents):
        use(part.text)                             # the common case in this project
    else:                                          # BlobResourceContents
        data = base64.b64decode(part.blob)         # mimeType says how to interpret it
```

## Why a list, and what `blob` is *actually* for

Two easy misreadings of this schema:

- **The list is not a curated multimodal bundle.** `contents` is a list because
  **one URI read can yield multiple parts** — the canonical case is a directory-like
  / aggregate resource returning several files, each its own
  `Text`/`BlobResourceContents` with its own `uri` + `mimeType`. It is "this read
  produced N pieces," *not* "here is a pre-assembled text+image prompt." (Resources
  don't paginate — that's `list_*` + `nextCursor`; this multiplicity is purely
  one-URI→many-parts.)
- **`blob` is general binary transport, not a "VLM channel."** Text-vs-blob is an
  *encoding* split (UTF-8 string vs base64 bytes), not a modality slot. A `blob` +
  `mimeType` carries *any* non-text resource — image, PDF, audio, archive. Images
  for a vision model are just one downstream use.

**Who assembles model context? The host — not MCP.** `read_resource` hands you raw
parts; *you* decide what reaches the model and convert it. MCP performs no modality
mapping. For a vision model on Anthropic, a `blob` becomes an image block yourself:

```python
{"type": "image",
 "source": {"type": "base64", "media_type": part.mimeType, "data": part.blob}}
# (a PDF blob → an Anthropic `document` block instead)
```

> When resource bytes are meant to flow *into a model-facing message* (inside a
> **tool result** or a **prompt message**), MCP wraps them in an `EmbeddedResource`
> content block — that's the spec's "resource → model" path. Plain `read_resource`
> (the app-controlled fetch) just returns raw `contents`; surfacing them is on you.
> See [[mcp-resource-access]].

> In *this* project the research resources (`papers://folders`, `papers://{topic}`)
> return markdown, so a read shows a **single** `TextResourceContents` — the
> blob/multi-part machinery is general MCP this server never exercises.

## vs. a tool result

| | [[mcp-tool-result]] (`CallToolResult`) | resource read (`ReadResourceResult`) |
|---|---|---|
| trigger | model decides (`tool_use`) | app/user decides — see [[mcp-resource-access]] |
| payload | `content` blocks (+ optional `structuredContent`) | `contents`: text / blob parts |
| error signal | `isError` flag | **none** — a failed read *raises* |

A resource read has **no `isError` channel**: there's no "logic-level failure" to
report — the fetch either returns `contents` or raises, so wrap it in `try/except`
rather than checking a flag.

> [!tip] Phone takeaway
> `read_resource(uri)` → `ReadResourceResult.contents`, a **list** of
> `TextResourceContents` (`.text`) or `BlobResourceContents` (`.blob`, base64).
> Branch on text vs blob, honour `mimeType`; **no `isError`** — failures raise.
> The list = one-URI→many-parts (not a multimodal bundle); `blob` = any binary
> (not a VLM channel); **the host** maps it into the model's image/document block.

Related: [[mcp-resource-access]] · [[resources]] · [[mcp-tool-result]] · [[mcp-session-init]] · [[08-adding-prompt-and-resource-features]]
