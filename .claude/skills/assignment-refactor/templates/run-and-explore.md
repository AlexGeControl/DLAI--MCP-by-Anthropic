## Run & Explore

> This section is emitted by the `assignment-refactor` skill so the assignment is
> runnable without tribal knowledge. All operations go through the `Makefile`.

### Quick start
```bash
make setup     # create .venv (uv) and install the package editable + dev deps
make test      # offline autograder — no network, no API key
make smoke     # confirm the server registers its tools/resources/prompts
```

### Explore in the MCP Inspector (web UI)
```bash
make inspect
```
This launches your server (stdio) **and** the MCP Inspector, and prints a
tokenized URL like:
```
🚀 MCP Inspector is up and running at:
   http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=<token>
```
Open it in your browser, click **Connect**, then:

1. **Tools → List Tools** → run `search_papers` (e.g. `topic=transformers`).
   This calls the *real* arXiv API (needs internet, **no key**) and writes
   `papers/<topic>/papers_info.json`.
2. **Resources → List** → read `papers://folders`, then `papers://{topic}` with
   the topic you just searched, to see the rendered output.
3. **Prompts** → list and run prompts. *Unimplemented stub prompts will raise —
   that's expected until you implement them.*

### Remote transport (Streamable HTTP — the modern remote path)
```bash
make serve-http        # serves http://localhost:8001/mcp
```
Then run `npx @modelcontextprotocol/inspector` with **no command**, choose the
**Streamable HTTP** transport, and connect to that URL.

### Run the chatbot for real
```bash
export ANTHROPIC_API_KEY=...   # or a .env file
make chatbot
```

> **Notes / gotchas**
> - arXiv needs network but **no API key**; only the chatbot needs `ANTHROPIC_API_KEY`.
> - `make smoke` runs the server *without* a transport, so it returns immediately —
>   `make serve`/`make inspect` block (they're long-running), as expected.
> - If `make setup` fails on a *"Readme file does not exist"* build error, the
>   package dir is missing its own `README.md` (see the skill's packaging note).
