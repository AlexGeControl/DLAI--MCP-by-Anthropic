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
from collections import defaultdict
from typing import Any

from anthropic import AsyncAnthropic
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .config import load_server_config

DEFAULT_MODEL = "us/aws/anthropic/eccn-claude-opus-4-8"
MAX_TOKENS = 10240
MAX_TOOL_CALLS = 10

class MCPChatBot:
    """A chatbot that connects to one or more MCP servers over stdio."""

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self.exit_stack = AsyncExitStack()
        #
        # TODO(lesson 06): use the ASYNC client. Do NOT use nest_asyncio.
        # per Claude Code: the client initialization below will parse the following two env. vars. automatically:
        # - ANTHROPIC_BASE_URL
        # - ANTHROPIC_API_KEY
        # 
        # The Anthropic inference API client
        self.anthropic = AsyncAnthropic()
        # The model ID
        self.model = model
        # The capacity registry
        self.available_capabilities: defaultdict[
            str, dict[str, Any]
        ] = defaultdict(dict)
        # The MCP session registry
        self.sessions: dict[str, ClientSession] = {}

    def _enclose_name(
        self,
        util_name: str,
        server_name: str
    ) -> str:
        """ Enclose the utility name with the MCP server name.

        Anthropic utility names must match ^[a-zA-Z0-9_-]{1,128}$
        so we use '__' as the server/utility delimiter rather than '@'/'/'.
        """
        return f"{server_name}__{util_name}"

    def _disclose_name(
        self,
        namespaced_util_name: str
    ) -> tuple[str, str]:
        """ Disclose the utility name from the MCP server name.

        Inverse of :meth:`_enclose_name`; splits on the first '__'.
        """
        server_name, _, util_name = namespaced_util_name.partition("__")
        return (server_name, util_name)

    async def _safe_list_capability(
        self,
        list_call, 
        server_name, 
        label
    ):
        """Run a list_*() call, swallowing failures into a skipped registration."""
        try:
            return await list_call()
        except Exception as e:                    # not asyncio.CancelledError (BaseException)
            print(f"[{server_name}] {label} discovery failed: {e}")
            return None

    async def _register_tools(
        self, 
        session,
        server_name,
    ):
        """Register MCP tools"""
        result = await self._safe_list_capability(session.list_tools, server_name, "tools")
        for tool in (result.tools if result else []):
            namespaced_tool_name = self._enclose_name(tool.name, server_name)
            self.available_capabilities["tools"][namespaced_tool_name] = {
                "name": namespaced_tool_name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }

    async def _register_resources(
        self,
        session,
        server_name,
    ):
        """Register MCP resources"""
        # Register non-templated resources:
        result = await self._safe_list_capability(session.list_resources, server_name, "resources")
        for resource in (result.resources if result else []):
            # Here we assume the resource URI is globally unique
            # as the file name in a typical Claude Code workspace
            self.available_capabilities["resources"][str(resource.uri)] = {
                "name": resource.name,
                "description": resource.description,
                # type(resource.uri): AnyUrl
                "uri": str(resource.uri),
                "server_name": server_name
            }
        # Register templated resources:
        result = await self._safe_list_capability(session.list_resource_templates, server_name, "resource templates")
        for resource_template in (result.resourceTemplates if result else []):
            # Here we assume the resource template URI is globally unique
            # as the file name in a typical Claude Code workspace
            self.available_capabilities["resources"][resource_template.uriTemplate] = {
                "name": resource_template.name,
                "description": resource_template.description,
                # type(resource.uriTemplate): str
                "uri": resource_template.uriTemplate,
                "server_name": server_name
            }

    async def _register_prompts(
        self,
        session,
        server_name,
    ):
        """Register MCP prompts"""
        # Register non-templated resources:
        result = await self._safe_list_capability(session.list_prompts, server_name, "prompts")
        for prompt in (result.prompts if result else []):
            # Here we assume the prompt name is globally unique
            # as the command name in a typical Claude Code workspace
            self.available_capabilities["prompts"][prompt.name] = {
                "name": prompt.name,
                "description": prompt.description,
                "arguments": prompt.arguments,
                "server_name": server_name
            }

    async def connect_to_server(
        self, server_name: str, server_config: dict[str, Any]
    ) -> None:
        """Spawn one stdio server and register its tools/prompts/resources."""
        # TODO(lesson 06/07): open a stdio_client + ClientSession via the
        # exit_stack, initialize the session, then list_tools/list_prompts/
        # list_resources and record each name/URI -> session in self.sessions
        # (and append tool/prompt metadata to the available_* lists).
        # Init MCP server params
        server_params = StdioServerParameters(**server_config)

        # Init stdio client subprocess
        (read_stream, write_stream) = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        
        # Init MCP session
        session = await self.exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        init = await session.initialize()

        # Register tools
        if init.capabilities.tools is not None:
            await self._register_tools(session, server_name)

        # Register resources
        if init.capabilities.resources is not None:
            await self._register_resources(session, server_name)

        # TODO: Register prompts
        if init.capabilities.prompts is not None:
            await self._register_prompts(session, server_name)

        # Update session registry
        self.sessions[server_name] = session
    
    async def connect_to_servers(
        self, config_path: str = "server_config.json"
    ) -> None:
        """Connect to every server declared in the config file."""
        # TODO(lesson 07): load the config via load_server_config and call
        # connect_to_server for each entry in data["mcpServers"].
        config = load_server_config(config_path)
        for server_name, srv_cfg in config["mcpServers"].items():
            await self.connect_to_server(server_name, srv_cfg)

    async def process_query(self, query: str | list[dict[str, str]]) -> None:
        """Run an agentic loop: call Claude, dispatch tool calls, repeat."""
        # 
        # TODO(lesson 06): loop
        # - `await self.anthropic.messages.create(...)`,
        # - print text blocks,
        # - for each tool_use block look up the session,
        # - `await session.call_tool(...)`,
        # - feed a tool_result back.
        # Break when the model stops requesting tools.
        #
        if isinstance(query, str):
            messages = [
                {
                    "role": "user",
                    "content": query,
                },
            ]
        else:
            messages = query

        for _ in range(MAX_TOOL_CALLS):
            ai_message = await self.anthropic.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                # OpenAI -> Anthropic gotcha: pass in a system message as a dedicated string 
                # instead of one message in `messages` list
                system=(
                    "You are my content assistant. "
                    "Below is an overview of avaiable tools: \n"
                    "- 'research__*': Get research paper overview from arXiv.\n"
                    "- 'fetch__*': Fetch URL from web as local Markdown file.\n"
                    "- 'filesystem__*': General local file system operations.\n"
                    "If the user is not asking about the above three scopes, answer without calling a tool."
                ),
                messages=messages,
                tools=self.list_tools(),
                # OpenAI -> Anthropic gotcha: pass in a {"type": "auto"} object instead of "auto"
                tool_choice={"type": "auto"},
            )
            messages.append(
                {
                    "role": "assistant",
                    "content": ai_message.content,
                }
            )

            # Show AI response every turn
            for block in ai_message.content:
                if block.type == "text":
                    print("\nAssistant: ", block.text)

            # Break the loop when the model stops requesting tools
            # - end_turn
            # - pause_turn
            # - max_tokens
            # - refusal
            if ai_message.stop_reason != "tool_use":
                break
            
            # Per Anthropic spec, the tool calling result should be appended to the user content.
            user_content = []
            for block in ai_message.content:
                match block.type:
                    case "tool_use":
                        # Parse target MCP server and tool
                        namespaced_tool_name = block.name
                        # Parse tool use id:
                        tool_use_id = block.id
                        # Perform MCP tool call
                        tool_result_content = []
                        is_tool_error = False

                        try:
                            # Parse server and tool names
                            server_name, tool_name = self._disclose_name(namespaced_tool_name)
                            # Retrieve session for the target MCP server
                            session = self.sessions[server_name]
                            # Parse MCP tool calling arguments:
                            tool_arguments = block.input

                            # Call MCP tool
                            tool_call_message = await session.call_tool(
                                name=tool_name, 
                                arguments=tool_arguments
                            )
                            
                            # Parse tool result content:
                            for tool_result_block in tool_call_message.content:
                                match tool_result_block.type:
                                    case "text":
                                        tool_result_content.append(
                                            {
                                                "type": "text",
                                                "text": tool_result_block.text
                                            }
                                        )
                                    # TODO: handle other context types
                            is_tool_error = tool_call_message.isError
                        except Exception as e:
                            tool_result_content = f"{namespaced_tool_name} tool call failed with {e}"
                            is_tool_error = True

                        #
                        # Assemble tool result block
                        #
                        user_content.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                # Provide text fallback 
                                # when no text context is available from tool call
                                "content": tool_result_content or "(no text context)",
                                "is_error": is_tool_error,
                            }
                        )

            # Per Anthropic spec, the tool calling result should be appended to the user content.
            messages.append(
                {
                    "role": "user",
                    "content": user_content,
                }
            )
        else:
            print("\n[ABORTED]: Max tool calls reached without final answer. Abort the query.")

    def list_tools(self):
        """ List all available tools
        """
        return list(self.available_capabilities["tools"].values())

    async def get_resource(
        self, 
        resource_uri: str,
        template_args: dict[str, Any] = None,
    ) -> str:
        """Read and print an MCP resource by URI."""
        # TODO(lesson 08): find the session for resource_uri (with a papers://
        # fallback), `await session.read_resource(...)`, print the text.
        # Retrieve MCP server name:
        server_name = self.available_capabilities["resources"][resource_uri]["server_name"]
        # Retrieve session for the target MCP server
        session = self.sessions[server_name]
        if template_args is not None:
            resource_uri = resource_uri.format(**template_args)
        
        # Get resource
        resource_message = await session.read_resource(resource_uri)
        
        # TODO: handle non-text modality
        resouce_content = "\n".join(
            block.text for block in resource_message.contents if hasattr(block, "text")
        )

        return resouce_content

    def list_prompts(self) -> None:
        """Print all available prompts."""
        if not self.available_capabilities["prompts"]:
            print("No prompts available.")
            return
        
        # TODO(lesson 08): print self.available_prompts (name, description, args).
        print("Available Prompts:")
        for id, registered_prompt in enumerate(self.available_capabilities["prompts"].values(), start=1):
            print(f"No {id}.")
            print(f"Source: {registered_prompt['server_name']}")
            print(f"Name: {registered_prompt['name']}")
            print(f"Description: {registered_prompt['description']}")
            print("Arguments:")
            for argument in registered_prompt["arguments"]:
                print(f"  - name: {argument.name}")
                print(f"  - required: {argument.required}")
                print(f"  - description: {argument.description}")
                print()
            print()

    async def execute_prompt(self, prompt_name: str, args: dict[str, Any]) -> list[dict[str, str]]:
        """Fetch a prompt by name, then run its text as a query."""
        # TODO(lesson 08): `await session.get_prompt(...)`, extract the text from
        # the first message, then `await self.process_query(text)`.
        # Retrieve MCP server name:
        server_name = self.available_capabilities["prompts"][prompt_name]["server_name"]
        # Retrieve session for the target MCP server
        session = self.sessions[server_name]
        
        # Get prompt
        prompt_message = await session.get_prompt(
            prompt_name,
            args
        )

        # The target payload is the `.messages` field
        user_messages = [
            {
                "role": m.role,
                "content": m.content.text,
            } for m in prompt_message.messages if m.content.type == "text"
        ] 

        return user_messages

    async def chat_loop(self) -> None:
        """Interactive REPL: queries, @resources, and /prompt commands."""
        # TODO(lesson 07/08): read input lines then 
        # - handle 'quit'
        # - @resource syntax
        # /prompts and /prompt <name> <k=v>..., 
        # else process_query(query).
        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nHuman: ").strip()
                if not query:
                    continue

                if query.lower() == "quit":
                    break
                
                # Handle @resource syntax
                if query.startswith("@"):
                    topic = query[1:]
                    resource_uri = (
                        "papers://topics"
                        if topic == "topics"
                        else "papers://{topic}"
                    )
                    resource_content =await self.get_resource(
                        resource_uri,
                        template_args={
                            "topic": topic,
                        }
                    )
                    print(
                        f"@{resource_uri}:\n"
                        f"{resource_content}"
                    )
                    continue
                
                # Handle /prompts command
                if query.startswith("/"):
                    parts = query.split()
                    command = parts[0].lower()
                    
                    if command == "/prompts":
                        self.list_prompts()
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
                        query =await self.execute_prompt(prompt_name, args)
                        await self.process_query(query)
                    else:
                        print(f"Unknown command: {command}")
                    
                    continue

                await self.process_query(query)
            except Exception as exc:  # noqa: BLE001
                print(f"\nError: {exc}")

    async def cleanup(self) -> None:
        """Close all open sessions/transports."""
        # TODO(lesson 06): close the exit_stack.
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
