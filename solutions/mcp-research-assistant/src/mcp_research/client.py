"""Multi-server MCP chatbot client (modernized).

Changes from the course original (see MODERNIZATION.md):

* Uses ``AsyncAnthropic`` + ``await`` instead of the sync ``Anthropic`` client
  driven through a ``nest_asyncio.apply()`` monkey-patch (report item #6).
* Default model is ``claude-sonnet-4-6`` instead of the retired
  ``claude-3-7-sonnet-20250219`` (report item #2).
* Config loading is delegated to :func:`mcp_research.config.load_server_config`.
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
        self.anthropic = AsyncAnthropic()
        self.model = model
        self.available_tools: list[dict[str, Any]] = []
        self.available_prompts: list[dict[str, Any]] = []
        # Maps tool/prompt names and resource URIs -> the owning session.
        self.sessions: dict[str, ClientSession] = {}

    async def connect_to_server(
        self, server_name: str, server_config: dict[str, Any]
    ) -> None:
        """Spawn one stdio server and register its tools/prompts/resources."""
        try:
            server_params = StdioServerParameters(**server_config)
            read, write = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()

            response = await session.list_tools()
            for tool in response.tools:
                self.sessions[tool.name] = session
                self.available_tools.append(
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                )

            prompts_response = await session.list_prompts()
            if prompts_response and prompts_response.prompts:
                for prompt in prompts_response.prompts:
                    self.sessions[prompt.name] = session
                    self.available_prompts.append(
                        {
                            "name": prompt.name,
                            "description": prompt.description,
                            "arguments": prompt.arguments,
                        }
                    )

            resources_response = await session.list_resources()
            if resources_response and resources_response.resources:
                for resource in resources_response.resources:
                    self.sessions[str(resource.uri)] = session
        except Exception as exc:  # noqa: BLE001 - surface and continue
            print(f"Error connecting to {server_name}: {exc}")

    async def connect_to_servers(
        self, config_path: str = "server_config.json"
    ) -> None:
        """Connect to every server declared in the config file."""
        data = load_server_config(config_path)
        for server_name, server_config in data["mcpServers"].items():
            await self.connect_to_server(server_name, server_config)

    async def process_query(self, query: str) -> None:
        """Run an agentic loop: call Claude, dispatch tool calls, repeat."""
        messages: list[dict[str, Any]] = [{"role": "user", "content": query}]

        while True:
            response = await self.anthropic.messages.create(
                max_tokens=MAX_TOKENS,
                model=self.model,
                tools=self.available_tools,
                messages=messages,
            )

            assistant_content = []
            has_tool_use = False

            for content in response.content:
                if content.type == "text":
                    print(content.text)
                    assistant_content.append(content)
                elif content.type == "tool_use":
                    has_tool_use = True
                    assistant_content.append(content)
                    messages.append(
                        {"role": "assistant", "content": assistant_content}
                    )

                    session = self.sessions.get(content.name)
                    if not session:
                        print(f"Tool '{content.name}' not found.")
                        break

                    result = await session.call_tool(
                        content.name, arguments=content.input
                    )
                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": content.id,
                                    "content": result.content,
                                }
                            ],
                        }
                    )

            if not has_tool_use:
                break

    async def get_resource(self, resource_uri: str) -> None:
        """Read and print an MCP resource by URI."""
        session = self.sessions.get(resource_uri)

        # Fallback for templated papers:// URIs.
        if not session and resource_uri.startswith("papers://"):
            for uri, sess in self.sessions.items():
                if uri.startswith("papers://"):
                    session = sess
                    break

        if not session:
            print(f"Resource '{resource_uri}' not found.")
            return

        try:
            result = await session.read_resource(uri=resource_uri)
            if result and result.contents:
                print(f"\nResource: {resource_uri}")
                print("Content:")
                print(result.contents[0].text)
            else:
                print("No content available.")
        except Exception as exc:  # noqa: BLE001
            print(f"Error: {exc}")

    async def list_prompts(self) -> None:
        """Print all available prompts."""
        if not self.available_prompts:
            print("No prompts available.")
            return

        print("\nAvailable prompts:")
        for prompt in self.available_prompts:
            print(f"- {prompt['name']}: {prompt['description']}")
            if prompt["arguments"]:
                print("  Arguments:")
                for arg in prompt["arguments"]:
                    arg_name = (
                        arg.name if hasattr(arg, "name") else arg.get("name", "")
                    )
                    print(f"    - {arg_name}")

    async def execute_prompt(self, prompt_name: str, args: dict[str, Any]) -> None:
        """Fetch a prompt by name, then run its text as a query."""
        session = self.sessions.get(prompt_name)
        if not session:
            print(f"Prompt '{prompt_name}' not found.")
            return

        try:
            result = await session.get_prompt(prompt_name, arguments=args)
            if result and result.messages:
                prompt_content = result.messages[0].content
                if isinstance(prompt_content, str):
                    text = prompt_content
                elif hasattr(prompt_content, "text"):
                    text = prompt_content.text
                else:
                    text = " ".join(
                        item.text if hasattr(item, "text") else str(item)
                        for item in prompt_content
                    )
                print(f"\nExecuting prompt '{prompt_name}'...")
                await self.process_query(text)
        except Exception as exc:  # noqa: BLE001
            print(f"Error: {exc}")

    async def chat_loop(self) -> None:
        """Interactive REPL: queries, @resources, and /prompt commands."""
        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")
        print("Use @folders to see available topics")
        print("Use @<topic> to search papers in that topic")
        print("Use /prompts to list available prompts")
        print("Use /prompt <name> <arg1=value1> to execute a prompt")

        while True:
            try:
                query = input("\nQuery: ").strip()
                if not query:
                    continue
                if query.lower() == "quit":
                    break

                if query.startswith("@"):
                    topic = query[1:]
                    resource_uri = (
                        "papers://folders"
                        if topic == "folders"
                        else f"papers://{topic}"
                    )
                    await self.get_resource(resource_uri)
                    continue

                if query.startswith("/"):
                    parts = query.split()
                    command = parts[0].lower()
                    if command == "/prompts":
                        await self.list_prompts()
                    elif command == "/prompt":
                        if len(parts) < 2:
                            print(
                                "Usage: /prompt <name> <arg1=value1> <arg2=value2>"
                            )
                            continue
                        prompt_name = parts[1]
                        args = {}
                        for arg in parts[2:]:
                            if "=" in arg:
                                key, value = arg.split("=", 1)
                                args[key] = value
                        await self.execute_prompt(prompt_name, args)
                    else:
                        print(f"Unknown command: {command}")
                    continue

                await self.process_query(query)
            except Exception as exc:  # noqa: BLE001
                print(f"\nError: {exc}")

    async def cleanup(self) -> None:
        """Close all open sessions/transports."""
        await self.exit_stack.aclose()


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
