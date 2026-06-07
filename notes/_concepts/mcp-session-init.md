---
title: MCP session init & primitive registration
slug: mcp-session-init
tags: [concept, mcp, client, session]
---

# MCP session init & primitive registration

What `connect_to_server` in [[06-creating-an-mcp-client]] actually does: 
- Open one [[mcp-client]] [`ClientSession`] to one [[mcp-server]]
- **Handshake**
- Then **discover** its three primitives 
  - [[tools]]
  - [[resources]]
  - [[prompt-templates]]
- Finally, copy them into host-side registries. 

Two things must be right: the **call sequence**, and the **schema mapping** from each MCP return value to the registry entry your dispatch code later looks up.

## The workflow

```python
async with stdio_client(params) as (read, write):
    async with ClientSession(read, write) as session:
        # 1. handshake + capability negotiation
        init = await session.initialize()
        # 2. discover          
        tools     = await session.list_tools()         
        resources = await session.list_resources()
        templates = await session.list_resource_templates()
        prompts   = await session.list_prompts()
```

1. **`initialize()` → `InitializeResult`** — the mandatory handshake. Returns
    - `protocolVersion`
    - `serverInfo`
    - `instructions`
    - and crucially **`capabilities`**.
   Everything else must come *after* this awaits.

2. **`list_*()`** — one call per primitive kind. Each returns a *wrapper* object
   (the list is an attribute, not the result itself — the trap that made
   `for t in result` iterate the model's fields instead of the tools):

   | call | wrapper | the list attribute |
   |---|---|---|
   | `list_tools()` | `ListToolsResult` | `.tools` |
   | `list_resources()` | `ListResourcesResult` | `.resources` |
   | `list_resource_templates()` | `ListResourceTemplatesResult` | `.resourceTemplates` |
   | `list_prompts()` | `ListPromptsResult` | `.prompts` |

   Each wrapper also has `.nextCursor` — large servers **paginate**; loop on the
   cursor if you need every item.

> [!warning] Not every server supports every primitive
> `initialize()`'s `capabilities` says which of `tools` / `resources` / `prompts`
> the server offers. Calling `list_prompts()` on a server with no prompt capability
> (e.g. the `filesystem` or `fetch` reference servers in
> [[07-connecting-the-mcp-chatbot-to-reference-servers]]) **raises**. Guard each
> discovery call in `try/except` (or check `capabilities` first) so one bare server
> doesn't abort the whole connect.

## Checking server capabilities

`initialize()` returns an `InitializeResult` whose **`.capabilities`** is a
`ServerCapabilities`. (If you didn't keep the result, the session caches it —
`session.get_server_capabilities()` returns the same object.)

Each primitive is an **optional field: `None` ⇒ unsupported**, a sub-object ⇒
supported. The sub-object's flags are about *change notifications*, not whether
listing works — so gate on `is not None`, don't inspect the inner flags.

| field | type when supported | sub-flags | `None` means |
|---|---|---|---|
| `tools` | `ToolsCapability` | `listChanged` | no tools — skip `list_tools()` |
| `resources` | `ResourcesCapability` | `subscribe`, `listChanged` | no resources **or templates** — skip both list calls |
| `prompts` | `PromptsCapability` | `listChanged` | no prompts — skip `list_prompts()` |
| `logging` / `completions` / `experimental` / `tasks` | — | — | feature absent |

> Resource **templates** have no capability of their own — they live under
> `resources`, so gate `list_resource_templates()` on `caps.resources` too.

### Capability-gated discovery + try/except

Use **both**: 
- The capability gate skips the *expected* "this server has no prompts" case cleanly (no exception spam)
- And `try/except` still catches the *unexpected*
    - A server that advertises a primitive but errors
    - A transport blip
    - Or a version mismatch. 
Defense in depth across a multi-server host.

```python
init = await session.initialize()
caps = init.capabilities                     # or: session.get_server_capabilities()

async def _safe(list_call, label):
    """Run a list_*() call, swallowing failures into a skipped registration."""
    try:
        return await list_call()
    except Exception as e:                    # not asyncio.CancelledError (BaseException)
        print(f"[{server_name}] {label} discovery failed: {e}")
        return None

# --- tools ---
if caps.tools is not None:
    result = await _safe(session.list_tools, "tools")
    for tool in (result.tools if result else []):
        self.available_tools.append({
            "name": self._enclose_tool_name(tool.name, server_name),
            "description": tool.description,
            "input_schema": tool.inputSchema,
        })

# --- resources + templates (both gated on caps.resources) ---
if caps.resources is not None:
    result = await _safe(session.list_resources, "resources")
    for r in (result.resources if result else []):
        self.resource_to_session[str(r.uri)] = session
    result = await _safe(session.list_resource_templates, "resource templates")
    for tpl in (result.resourceTemplates if result else []):
        self.resource_to_session[tpl.uriTemplate] = session

# --- prompts ---
if caps.prompts is not None:
    result = await _safe(session.list_prompts, "prompts")
    for p in (result.prompts if result else []):
        self.available_prompts.append(
            {"name": p.name, "description": p.description, "arguments": p.arguments}
        )
        self.prompt_to_session[p.name] = session
```

For the reference servers in [[07-connecting-the-mcp-chatbot-to-reference-servers]],
the gate alone is enough (`filesystem`/`fetch` simply declare no `prompts`); the
`try/except` is the belt-and-suspenders layer for everything else.

## MCP return schemas → host registry entries

The discovered item carries MCP-side (often camelCase) fields; you only extract a few
and reshape them into the entry your host stores. 

The key transform is `inputSchema` → `input_schema` (see [[openai-to-anthropic-migration]] / [[anthropic-tool-use-schema]]).

### `Tool`
**Tool** (`name`, `title`, `description`, **`inputSchema`**, `outputSchema`, `annotations`, …) →
```python
self.available_tools.append({
    "name": self._enclose_tool_name(tool.name, server_name),  # server__tool, regex-safe
    "description": tool.description,
    "input_schema": tool.inputSchema,        # camelCase → snake_case
})
```

### Resource & ResourceTemplate
**Resource** (`uri`, `name`, `title`, `description`, `mimeType`, `size`) and
**ResourceTemplate** (**`uriTemplate`**, `name`, `description`, `mimeType`) →
store the addressable string and which session owns it:
```python
# concrete resources have a fixed `uri`; templates have a `uriTemplate` (papers://{topic})
self.resource_to_session[str(resource.uri)] = session          # for read_resource(uri)
```
> Concrete vs templated is a real split: `papers://folders` shows up in
> `list_resources()`
> but `papers://{topic}` only appears in `list_resource_templates()`. 
> List **both** or you'll miss the templated ones.

### Prompt
**Prompt** (`name`, `title`, `description`, **`arguments`**) where each
`PromptArgument` is (`name`, `description`, `required`) →
```python
self.available_prompts.append({
    "name": prompt.name,
    "description": prompt.description,
    "arguments": prompt.arguments,           # list[PromptArgument]
})
self.prompt_to_session[prompt.name] = session
```

## The routing problem (why registries differ per primitive)

`self.sessions` is keyed by **server name**, but the model/host later dispatches by
*tool name*, *resource URI*, or *prompt name* — none of which carry the server.
So registration must record enough to route back:

| primitive | dispatch key | how this client routes |
|---|---|---|
| tool | the namespaced name Claude returns | embed server in the name (`server__tool`), `_disclose_tool_name` recovers it → `sessions[server]` |
| resource | a `papers://…` URI | a `uri → session` map built at registration (URIs aren't namespaced) |
| prompt | a prompt name | a `name → session` map (or namespace prompt names too) |

The lesson: **whatever your dispatch looks up, build that index during
registration** — a connection map alone (`server → session`) isn't enough for
resources and prompts.

## Consuming the registered primitives (later)

- `await session.call_tool(name, arguments)` → `CallToolResult` — see [[mcp-tool-result]].
- `await session.read_resource(uri)` → `ReadResourceResult` (`.contents`) — see [[mcp-resource-result]]; the select/read/inject flow is [[mcp-resource-access]].
- `await session.get_prompt(name, arguments)` → `GetPromptResult` (`.messages`) — see [[mcp-prompt-result]]; the select/render/run flow is [[mcp-prompt-access]].
Then feed the message text back into `process_query` to run it.

> [!tip] Phone takeaway
> `initialize()` **first** (negotiates capabilities), then `list_tools` /
> `list_resources` / `list_resource_templates` / `list_prompts` — each returns a
> *wrapper* (`.tools`, `.resources`, …), not a bare list, and may **raise** if the
> server lacks that primitive. Reshape items into registry entries
> (`inputSchema`→`input_schema`), and build a **routing index** for whatever key
> dispatch uses (tool name / URI / prompt name).

Related: [[mcp-client]] · [[mcp-server]] · [[tools]] · [[resources]] · [[prompt-templates]] · [[mcp-tool-result]] · [[anthropic-tool-use-schema]] · [[06-creating-an-mcp-client]] · [[07-connecting-the-mcp-chatbot-to-reference-servers]] · [[08-adding-prompt-and-resource-features]]
