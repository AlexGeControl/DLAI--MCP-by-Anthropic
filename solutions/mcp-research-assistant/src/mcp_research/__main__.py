"""CLI entrypoint for mcp_research.

Usage:
    python -m mcp_research server                       # stdio (default)
    python -m mcp_research server --transport streamable-http
    python -m mcp_research chatbot [--config PATH]
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mcp_research")
    sub = parser.add_subparsers(dest="command", required=True)

    server_p = sub.add_parser("server", help="Run the research MCP server.")
    server_p.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="Transport to serve on (default: stdio).",
    )

    chatbot_p = sub.add_parser("chatbot", help="Run the MCP chatbot client.")
    chatbot_p.add_argument(
        "--config",
        default="server_config.json",
        help="Path to the MCP server config (default: server_config.json).",
    )

    args = parser.parse_args(argv)

    if args.command == "server":
        from .server import main as server_main

        server_main(transport=args.transport)
        return 0

    if args.command == "chatbot":
        import asyncio

        from .client import run

        asyncio.run(run(args.config))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
