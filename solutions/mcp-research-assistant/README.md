# Assignment: MCP Research Assistant

Build an **arXiv research assistant** as a Model Context Protocol (MCP) system:
a **server** that exposes 
- Paper-search tools
- A browsable **resource**, and 
- A reusable **prompt**, 

Plus a multi-server **chatbot client** that an LLM drives to 
- Search
- Store, and 
- Synthesize academic papers.

This assignment is the capstone of the MCP course. It ties together everything
from [[05-creating-an-mcp-server]] through
[[10-creating-and-deploying-remote-servers]].

## Background

MCP standardizes how an LLM application talks to external capabilities. A
**server** advertises three primitives:

- **Tools** — model-callable functions (here: `search_papers`, `extract_info`).
- **Resources** — read-only, URI-addressed data (here: `papers://folders` and
  `papers://{topic}`). See [[08-adding-prompt-and-resource-features]].
- **Prompts** — reusable, parameterized instruction templates (here:
  `generate_search_prompt`).

A **client** ([[06-creating-an-mcp-client]]) connects to one or more servers over
a transport (`stdio` locally; `streamable-http` remotely), discovers their
primitives, and exposes them to the model. The chatbot connects to several
reference servers at once ([[07-connecting-the-mcp-chatbot-to-reference-servers]],
[[09-configuring-servers-for-claude-desktop]]).

## Learning goals

1. Decompose an MCP server into **pure logic** vs. a thin **protocol adapter**.
2. Implement tools, a templated resource, and a prompt with `FastMCP`.
3. Write an **async** multi-server MCP client using `AsyncAnthropic`.
4. Run a server over both **stdio** and **streamable-http** transports.
5. Make external-service code **testable offline** via dependency injection.

## Project layout

```
src/mcp_research/
  arxiv_tools.py   # PURE logic: search/store/extract/render. The gradeable core.
  server.py        # FastMCP wrapper: tools + resources + prompt; stdio/http entry.
  config.py        # load_server_config(path) -> dict
  client.py        # async MCP chatbot (AsyncAnthropic, no nest_asyncio)
  __main__.py      # CLI: `server` and `chatbot` subcommands
tests/             # pytest autograder (offline unit + gated integration)
```

## The tasks (what to implement)

You are given this README, the test suite, full docstring contracts, and stubs
that `raise NotImplementedError`. Implement, in roughly this order:

### Task 1 — Pure research logic (`src/mcp_research/arxiv_tools.py`) — graded offline
Relevant: [[05-creating-an-mcp-server]], [[08-adding-prompt-and-resource-features]]

- `search_papers(topic, max_results, *, client=None, search_factory=None, paper_dir)`
  — query arXiv and persist metadata under
  `<paper_dir>/<topic_slug>/papers_info.json`. **Import `arxiv` lazily**, only
  when no `client`/`search_factory` is injected. Re-running for a topic merges.
- `extract_info(paper_id, *, paper_dir)` — search every topic folder for the id.
- `list_topic_folders`, `available_folders_markdown`, `topic_papers_markdown`,
  `generate_search_prompt` — the resource/prompt rendering helpers.

> Why dependency injection? It lets the autograder pass a fake arXiv client, so
> the unit tests need **no network, no API key, and no third-party packages**.
> Keep `arxiv_tools.py` free of top-level third-party imports.

### Task 2 — Config loading (`src/mcp_research/config.py`) — graded offline
Relevant: [[09-configuring-servers-for-claude-desktop]]

- `load_server_config(path)` — parse + validate the `mcpServers` config.

### Task 3 — MCP server (`src/mcp_research/server.py`) — integration
Relevant: [[05-creating-an-mcp-server]], [[10-creating-and-deploying-remote-servers]]

- Wire each `@mcp.tool`/`@mcp.resource`/`@mcp.prompt` handler to its
  `arxiv_tools` function. `main(transport)` runs `stdio` or `streamable-http`.

### Task 4 — Async chatbot client (`src/mcp_research/client.py`) — integration
Relevant: [[06-creating-an-mcp-client]], [[07-connecting-the-mcp-chatbot-to-reference-servers]]

- Implement `MCPChatBot`: connect to servers, run the tool-use loop with
  `AsyncAnthropic`, handle `@resource` and `/prompt` REPL commands. Use
  `claude-sonnet-4-6`; do **not** use `nest_asyncio`.

## How to run the tests

The unit tests (Tasks 1–2) are **offline and dependency-free** — only `pytest`:

```bash
cd solutions/mcp-research-assistant
python -m pytest tests/test_arxiv_tools.py tests/test_config.py -q
```

The integration tests (Task 3) need the optional deps; they auto-skip if `mcp`
is not importable:

```bash
pip install -e ".[dev]"
python -m pytest -q          # full suite
```

## How to run it for real

```bash
pip install -e .
export ANTHROPIC_API_KEY=...        # or put it in a .env file

# Run the server directly over stdio (default) or streamable-http:
python -m mcp_research server
python -m mcp_research server --transport streamable-http

# Run the chatbot (spawns the servers listed in server_config.json):
python -m mcp_research chatbot
```

In the chatbot REPL: type a query, `@folders` / `@<topic>` to read resources,
`/prompts` to list prompts, `/prompt generate_search_prompt topic=... num_papers=...`
to run one. Type `quit` to exit.

See [`MODERNIZATION.md`](./MODERNIZATION.md) for what changed versus the original
course code and why.
