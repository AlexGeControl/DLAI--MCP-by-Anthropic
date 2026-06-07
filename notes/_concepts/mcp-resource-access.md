---
title: Reading & using MCP resources
slug: mcp-resource-access
tags: [concept, mcp, resources]
---

# Reading & using MCP resources

The resource counterpart of [[anthropic-tool-use-schema]] — *how a resource gets
selected, read, and fed to the model*. The crucial asymmetry, up front:

> **A resource has no Messages API representation.** Unlike a `tool_use` block
> (model-driven, part of the Anthropic request/response), the LLM never "calls" a
> resource. Resources are **application-controlled** (see [[resources]]): the host
> reads them and decides whether to inject the contents into context.

So "resource use" is **read + inject**, not a model turn.

## Who selects? (not the model, by default)

| mechanism | who picks | when |
|---|---|---|
| `@resource` REPL syntax | the **user** | the course/assignment default |
| promote resource → [[tools|tool]] | the **model**, via the existing [[tool-use-loop]] | when you want autonomy — reuse the loop, don't build a selector |
| bespoke LLM "selector" call | — | over-engineering; duplicates `tool_choice` |

The takeaway: don't invent a parallel selector — either the **user** picks via `@`,
or you **expose the resource as a tool** so the loop you already have selects it.

## The access workflow

```python
# 1. resolve the URI (concrete vs templated)
uri = registry[name]["uri"]                  # "papers://folders"  OR  "papers://{topic}"
if template_args:
    uri = uri.format(**template_args)         # "papers://{topic}" → "papers://quantum"
# 2. read — read_resource accepts AnyUrl | str (it coerces a str)
result = await session.read_resource(uri)     # → ReadResourceResult, see [[mcp-resource-result]]
# 3. inject the text into context YOURSELF (resources aren't a model turn)
text = "\n".join(p.text for p in result.contents if hasattr(p, "text"))
```

## URI addressing: concrete vs templated

- **Concrete** (`papers://folders`) — a fixed address, discovered via `list_resources()`.
- **Templated** (`papers://{topic}`) — an RFC 6570 template, discovered via
  `list_resource_templates()`; fill the variables before reading. `str.format`
  covers simple `{var}` slots; full RFC 6570 has richer syntax (`{?query}`, …).

See [[mcp-session-init]] for how both kinds get registered and routed.

## Injecting into context

Resources carry **reference data, not instructions**. The typical pattern: read the
text and prepend/append it to the next `user` message (or a system note) so the
model can ground its answer on it. **You own this step** — nothing flows back
automatically the way a `tool_result` re-enters the [[tool-use-loop]].

> [!tip] Phone takeaway
> Resources are **app/user-controlled** with **no Messages API block**. Flow: pick
> (user `@`, or promote-to-tool) → resolve URI (`.format` for templates) →
> `read_resource` → inject the `.text` into context yourself.

Related: [[mcp-resource-result]] · [[resources]] · [[anthropic-tool-use-schema]] · [[mcp-session-init]] · [[tool-use-loop]] · [[06-creating-an-mcp-client]] · [[08-adding-prompt-and-resource-features]]
