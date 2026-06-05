"""Multi-server MCP chatbot client (modernized).

Changes from the course original (see MODERNIZATION.md):

* Uses ``AsyncAnthropic`` + ``await`` instead of the sync ``Anthropic`` client
  driven through a ``nest_asyncio.apply()`` monkey-patch (report item #6).
* Default model is ``claude-sonnet-4-6`` instead of the retired
  ``claude-3-7-sonnet-20250219`` (report item #2).
* Config loading is delegated to :func:`mcp_research.config.load_server_config`.

See [[06-creating-an-mcp-client]] and
[[07-connecting-the-mcp-chatbot-to-reference-servers]].
"""

from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack
from typing import Any

from anthropic import AsyncAnthropic
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .config import load_server_config

DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 2024


class MCPChatBot:
    """A chatbot that connects to one or more MCP servers over stdio."""

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self.exit_stack = AsyncExitStack()
        # TODO(lesson 06): use the ASYNC client. Do NOT use nest_asyncio.
        self.anthropic = AsyncAnthropic()
        self.model = model
        self.available_tools: list[dict[str, Any]] = []
        self.available_prompts: list[dict[str, Any]] = []
        self.sessions: dict[str, ClientSession] = {}

    async def connect_to_server(
        self, server_name: str, server_config: dict[str, Any]
    ) -> None:
        """Spawn one stdio server and register its tools/prompts/resources."""
        # TODO(lesson 06/07): open a stdio_client + ClientSession via the
        # exit_stack, initialize the session, then list_tools/list_prompts/
        # list_resources and record each name/URI -> session in self.sessions
        # (and append tool/prompt metadata to the available_* lists).
        raise NotImplementedError("Implement connect_to_server")

    async def connect_to_servers(
        self, config_path: str = "server_config.json"
    ) -> None:
        """Connect to every server declared in the config file."""
        # TODO(lesson 07): load the config via load_server_config and call
        # connect_to_server for each entry in data["mcpServers"].
        raise NotImplementedError("Implement connect_to_servers")

    async def process_query(self, query: str) -> None:
        """Run an agentic loop: call Claude, dispatch tool calls, repeat."""
        # TODO(lesson 06): loop — `await self.anthropic.messages.create(...)`,
        # print text blocks, and for each tool_use block look up the session,
        # `await session.call_tool(...)`, and feed a tool_result back. Break
        # when the model stops requesting tools.
        raise NotImplementedError("Implement process_query")

    async def get_resource(self, resource_uri: str) -> None:
        """Read and print an MCP resource by URI."""
        # TODO(lesson 08): find the session for resource_uri (with a papers://
        # fallback), `await session.read_resource(...)`, print the text.
        raise NotImplementedError("Implement get_resource")

    async def list_prompts(self) -> None:
        """Print all available prompts."""
        # TODO(lesson 08): print self.available_prompts (name, description, args).
        raise NotImplementedError("Implement list_prompts")

    async def execute_prompt(self, prompt_name: str, args: dict[str, Any]) -> None:
        """Fetch a prompt by name, then run its text as a query."""
        # TODO(lesson 08): `await session.get_prompt(...)`, extract the text from
        # the first message, then `await self.process_query(text)`.
        raise NotImplementedError("Implement execute_prompt")

    async def chat_loop(self) -> None:
        """Interactive REPL: queries, @resources, and /prompt commands."""
        # TODO(lesson 07/08): read input lines; handle 'quit', @resource syntax,
        # /prompts and /prompt <name> <k=v>..., else process_query(query).
        raise NotImplementedError("Implement chat_loop")

    async def cleanup(self) -> None:
        """Close all open sessions/transports."""
        # TODO(lesson 06): close the exit_stack.
        raise NotImplementedError("Implement cleanup")


async def run(config_path: str = "server_config.json") -> None:
    """Wire up the chatbot, connect to servers, and start the REPL."""
    load_dotenv()
    chatbot = MCPChatBot()
    try:
        await chatbot.connect_to_servers(config_path)
        await chatbot.chat_loop()
    finally:
        await chatbot.cleanup()


def main() -> None:
    """Synchronous entrypoint."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
