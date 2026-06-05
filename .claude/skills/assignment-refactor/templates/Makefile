# Dev harness for the generated MCP assignment.
# Emitted by the `assignment-refactor` skill. Substitute PKG below if the
# package import name differs from `mcp_research`.

PKG   ?= mcp_research
VENV  ?= .venv
PY    := $(VENV)/bin/python
PORT  ?= 8001

.PHONY: help setup test smoke serve serve-http inspect chatbot clean
.DEFAULT_GOAL := help

help:  ## List targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup:  ## Create the venv (uv) and install the package editable + dev deps
	uv venv $(VENV) --python 3.12
	uv pip install -e ".[dev]" --python $(PY) || uv pip install -e . --python $(PY)

test:  ## Run the OFFLINE autograder (no network, no API key)
	$(PY) -m pytest tests/test_arxiv_tools.py tests/test_config.py -q

smoke:  ## Verify the server registers its tools/resources/prompts (no transport)
	$(PY) scripts/smoke_server.py $(PKG).server

serve:  ## Run the MCP server over stdio
	$(PY) -m $(PKG) server

serve-http:  ## Run the MCP server over streamable-http (http://localhost:$(PORT)/mcp)
	$(PY) -m $(PKG) server --transport streamable-http

inspect:  ## Launch the MCP Inspector web UI wrapping the stdio server
	npx @modelcontextprotocol/inspector $(PY) -m $(PKG) server

chatbot:  ## Run the MCP chatbot client (needs ANTHROPIC_API_KEY)
	$(PY) -m $(PKG) chatbot

clean:  ## Remove the venv and caches
	rm -rf $(VENV) .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
