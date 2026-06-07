---
lesson: 6
slug: pnd5n
title: Creating an MCP Client
type: video_notebook
duration_min: 9.2
video_id: 888
transcript: raw/transcripts/06-creating-an-mcp-client.md
notebook: raw/assignments/L5/L5.ipynb
source_code: raw/assignments/L5/mcp_project/mcp_chatbot.py
status: notes-complete

# --- knowledge-graph metadata ---
concepts:
  - mcp-client
  - stdio-transport
  - tool-use-loop
  - mcp-host
  - mcp-session-init
prerequisites:
  - "[[05-creating-an-mcp-server]]"    # the server this client connects to
  - "[[04-chatbot-example]]"           # the tool-use loop reused here
related:
  - "[[03-mcp-architecture]]"
  - "[[mcp-inspector]]"                # the client replaces the inspector as the way to drive the server
  - "[[mcp-session-init]]"             # full connect/discover/route workflow
  - "[[mcp-tool-result]]"              # CallToolResult schema
  - "[[mcp-resource-access]]"          # select/resolve/read/inject
  - "[[mcp-resource-result]]"          # ReadResourceResult schema
  - "[[mcp-prompt-access]]"            # discover/invoke/run
  - "[[mcp-prompt-result]]"            # GetPromptResult schema
  - "[[mcp-control-model]]"            # why primitives surface differently
  - "[[anthropic-tool-use-schema]]"    # Anthropic message shapes
  - "[[openai-to-anthropic-migration]]"  # SDK gotchas
leads_to:
  - "[[07-connecting-the-mcp-chatbot-to-reference-servers]]"  # next: one client → many servers
tags: [mcp, client, stdio, asyncio, session]
---

# Lesson 6 — Creating an MCP Client

> **One-line:** Replace the [[mcp-inspector]] with your own [[mcp-client]] inside the chatbot: open a
> `ClientSession` over a `stdio_client` connection to the Lesson-5 server, run
> `initialize → list_tools → call_tool`, and feed results back through the same [[tool-use-loop]].

## Concept map

```mermaid
graph TD
    H[MCP host = chatbot process] --> C[MCP client / ClientSession]
    C -->|stdio_client launches subprocess| S[research_server.py]
    C -->|1. initialize| S
    C -->|2. list_tools| S
    S -->|tool names + schemas| C
    C --> AV[available_tools passed to Claude]
    AV --> LOOP[tool-use loop]
    LOOP -->|3. call_tool name,args| S
    S -->|result.content| LOOP
```

## Why this lesson exists

[[05-creating-an-mcp-server]] built the server and tested it by hand with the [[mcp-inspector]].

This lesson builds the **other half of the split** introduced in [[03-mcp-architecture]]: a real
[[mcp-client]] living inside a [[mcp-host]] (the chatbot). 

The chat loop from [[04-chatbot-example]]
returns almost unchanged — the only difference is *where tool results come from*: 
- A server over a transport
- Instead of a local function call.

## Key ideas

### [[mcp-client]] inside a [[mcp-host]]
The host is the app the user talks to (the chatbot); the client is the component inside it that
holds **one connection to one server**. 

The course flags this code as deliberately *lower-level* —
you rarely hand-write clients, but it shows what Claude Desktop / Cursor do under the hood.

### Crucially: **no tools are defined here**
Compare with [[04-chatbot-example]], which hard-coded a `tools` list. Now the client *asks the
server* what tools exist. The client's job is to **query for tools and hand them to the LLM**.

### The connection lifecycle (the heart of the lesson)
From `raw/assignments/L5/mcp_project/mcp_chatbot.py`:

```python
server_params = StdioServerParameters(
    command="uv", args=["run", "research_server.py"], env=None,
)
async with stdio_client(server_params) as (read, write):     # launch server as subprocess
    async with ClientSession(read, write) as session:
        await session.initialize()                            # 1. handshake + capability negotiation
        response = await session.list_tools()                 # 2. returns ListToolsResult wrapper
        self.available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema,                 # camelCase → snake_case; schema from FastMCP
        } for tool in response.tools]                        # iterate .tools — NOT response itself
```

The course shows tools only. A production host also calls `list_resources()`,
`list_resource_templates()`, and `list_prompts()` — each returning its own wrapper (`ListResourcesResult`,
etc.) — and **gates every call on `initialize()`'s capability flags** so bare servers don't abort the
connect.

> Full details — wrapper types, capability-gating, `try/except` pattern, routing registries,
> `inputSchema` → `input_schema` reshape, and resources/prompts registration:
> **[[mcp-session-init]]**

### Same [[tool-use-loop]], remote execution
In `process_query`, the one changed line is how a tool runs:

```python
# Lesson 4:  result = execute_tool(tool_name, tool_args)
result = await self.session.call_tool(tool_name, arguments=tool_args)   # 3. call over MCP
```

The server invokes the tool; `result` is a `CallToolResult` (`.content` list, `.isError` flag).
The host appends a `tool_result` block and calls the model again until `stop_reason != "tool_use"`.

> MCP's `CallToolResult` schema (`.content`, `.structuredContent`, `.isError`): **[[mcp-tool-result]]**  
> Anthropic `tool_use` / `tool_result` message shapes + the full agentic loop: **[[anthropic-tool-use-schema]]**

## Mechanics / walkthrough

1. `__init__` starts with **no session and no tools** — both filled in once connected.
2. `connect_to_server_and_run` opens `stdio_client` → `ClientSession` as nested async context
   managers, runs the lifecycle above, then enters `chat_loop`.
3. Everything is `async` (`asyncio.run(main())`); `call_tool` and `list_tools` are awaited.
4. Run it: `cd` into the project, `source .venv/bin/activate`, then `uv run mcp_chatbot.py`.
   On startup you'll see the `list_tools` request fire; querying ("search physics, 2 papers")
   fires a `call_tool` request to the server.

> [!warning] Staleness
> This client uses the **sync `Anthropic` client + `nest_asyncio.apply()` hack** inside async code,
> the **retired model id** `claude-3-7-sonnet-20250219`, and ships a junk `typing` PyPI pin. 
> 
> Modern Fix: use `AsyncAnthropic` + `await self.anthropic.messages.create(...)`, drop `nest_asyncio`, switch
> to `claude-sonnet-4-6`, and remove the `typing` dependency. 
> 
> See `reports/modernization.md` #2, #5, #6.

## Connections
- ⬅ Connects to the server from [[05-creating-an-mcp-server]]; reuses the loop from [[04-chatbot-example]]
- ➡ Generalized to **many servers via config** in [[07-connecting-the-mcp-chatbot-to-reference-servers]]
- 📖 Vocabulary: [[mcp-client]], [[mcp-host]], [[stdio-transport]] (replaces [[mcp-inspector]])
- 🧩 **Session init & primitive registration** (the full connect/discover/route pattern): [[mcp-session-init]]
- 🔧 **Tool dispatch** — MCP result schema: [[mcp-tool-result]]; Anthropic message shapes: [[anthropic-tool-use-schema]]; agentic loop: [[tool-use-loop]]
- 📂 **Resource access** — select/resolve/read/inject flow: [[mcp-resource-access]]; `ReadResourceResult` schema: [[mcp-resource-result]]
- 💬 **Prompt access** — discover/invoke/run flow: [[mcp-prompt-access]]; `GetPromptResult` schema: [[mcp-prompt-result]]
- 🎛️ **Why tool/resource/prompt surface differently** in a real host: [[mcp-control-model]]
- ⚠️ SDK gotchas (base URL, `tool_choice`, tool-name regex): [[openai-to-anthropic-migration]]

> [!tip] Phone takeaway
> A client is: launch subprocess over **stdio** → `initialize` (capability handshake) →
> `list_tools / list_resources / list_prompts` (each returns a *wrapper*, iterate its attribute) →
> build routing registries → `call_tool / read_resource / get_prompt` on dispatch.
> The [[tool-use-loop]] driving Claude is unchanged from Lesson 4 — only *how results are fetched* changes.
