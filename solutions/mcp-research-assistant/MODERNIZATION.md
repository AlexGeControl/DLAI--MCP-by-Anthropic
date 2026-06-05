# Modernization deltas

Concrete changes made in this refactor versus the original course code
(`raw/assignments/L7/mcp_project/*` and `raw/assignments/L9/mcp_project/research_server.py`).
Each item is tied to a finding in [`reports/modernization.md`](../../reports/modernization.md).

| Report # | Change | Where |
|----------|--------|-------|
| **#1** (must-fix) | Dropped the deprecated standalone **`transport='sse'`** remote server. The server now runs `mcp.run(transport='streamable-http')` (selectable via the CLI) with `FastMCP("research", host="0.0.0.0", port=8001)`. | `src/mcp_research/server.py`, `src/mcp_research/__main__.py` |
| **#5** (must-fix) | Removed the harmful **`PyPI:typing`** backport pin. Never imported; shadows stdlib on 3.10+. Not present in `pyproject.toml`. | `pyproject.toml` |
| **#2** (should-fix) | Model id `claude-3-7-sonnet-20250219` → **`claude-sonnet-4-6`** (`DEFAULT_MODEL`). | `src/mcp_research/client.py` |
| **#6** (should-fix) | Replaced sync `Anthropic` + `nest_asyncio.apply()` with **`AsyncAnthropic`** and `await self.anthropic.messages.create(...)`. `nest_asyncio` import and call removed entirely. | `src/mcp_research/client.py` |
| **#3** (should-fix) | Bumped `mcp` floor to **`>=1.27`**. FastMCP / decorators / `ClientSession` / `stdio_client` APIs unchanged. | `pyproject.toml` |
| **#4** (should-fix) | Bumped `anthropic` floor to **`>=0.105`**. | `pyproject.toml` |
| **#7** (should-fix) | Removed dead/deprecated **`PyPI:PyPDF2`** dependency (never imported). | `pyproject.toml` |
| **#8** (keep) | Kept `arxiv>=2.2` and `python-dotenv>=1.1`. | `pyproject.toml` |

## Structural changes (refactor, beyond the report)

- **Decomposition.** The monolithic `research_server.py` is split into
  `arxiv_tools.py` (pure logic), `server.py` (MCP adapter), `config.py`
  (config loading), `client.py` (chatbot), and `__main__.py` (CLI). The original
  mixed I/O, the arXiv network call, MCP wiring, and markdown rendering in one file.
- **Dependency injection for offline grading.** `search_papers` accepts an
  injected `client` and `search_factory`; `arxiv` is imported *lazily* and only
  when nothing is injected. `arxiv_tools.py` has **no top-level third-party
  imports**, so the unit tests run with only pytest installed — no `arxiv`,
  `mcp`, or `anthropic` required.
- **`paper_dir` parameterization.** All filesystem functions take `paper_dir`
  so tests use a tmp dir instead of the hardcoded global `PAPER_DIR`.
- **Config loading extracted + validated.** `load_server_config` replaces the
  inline `open("server_config.json")` block and adds error handling.
- **`research` server command** in `server_config.json` now invokes
  `python -m mcp_research server` (the packaged entrypoint) instead of
  `uv run research_server.py`.

## Optional / not applied

- **#9** (Docker base bump): no Dockerfile is shipped in this baseline assignment;
  remote deployment is left as a stretch extension.
