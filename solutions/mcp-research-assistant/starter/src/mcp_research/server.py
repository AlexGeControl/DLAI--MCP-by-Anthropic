"""FastMCP server exposing the arXiv research tools, a resource, and a prompt.

This module is a thin adapter: every handler delegates to the pure functions in
``arxiv_tools``. It supports two transports:

* ``stdio`` — for local use (Claude Desktop, the bundled chatbot client).
* ``streamable-http`` — for remote deployment. This replaces the deprecated
  standalone ``sse`` transport from the original course (see MODERNIZATION.md).

See [[05-creating-an-mcp-server]], [[08-adding-prompt-and-resource-features]],
and [[10-creating-and-deploying-remote-servers]].
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import arxiv_tools

PAPER_DIR = arxiv_tools.PAPER_DIR

# TODO(lesson 10): build the FastMCP server. Set host="0.0.0.0" and port=8001
# so it can also serve over streamable-http (do NOT pass anything SSE-specific).
mcp = FastMCP(
    "research", 
    host="0.0.0.0", 
    port=8001
)


@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> list[str]:
    """Search for papers on arXiv based on a topic and store their information.

    Args:
        topic: The topic to search for.
        max_results: Maximum number of results to retrieve (default: 5).

    Returns:
        List of paper IDs found in the search.
    """
    # TODO(lesson 05): delegate to arxiv_tools.search_papers (paper_dir=PAPER_DIR).
    return arxiv_tools.search_papers(
        topic=topic, 
        max_results=max_results, 
        paper_dir=PAPER_DIR
    )


@mcp.tool()
def extract_info(paper_id: str) -> str:
    """Search for information about a specific paper across all topic directories.

    Args:
        paper_id: The ID of the paper to look for.

    Returns:
        JSON string with paper information if found, error message if not found.
    """
    # TODO(lesson 05): delegate to arxiv_tools.extract_info (paper_dir=PAPER_DIR).
    return arxiv_tools.extract_info(
        paper_id=paper_id, 
        paper_dir=PAPER_DIR
    )


@mcp.resource("papers://topics")
def get_available_topics() -> str:
    """List all available topics in the papers directory."""
    # TODO(lesson 08): delegate to arxiv_tools.available_folders_markdown.
    return arxiv_tools.available_folders_markdown(paper_dir=PAPER_DIR)


@mcp.resource("papers://{topic}")
def get_topic_papers(topic: str) -> str:
    """Get detailed information about papers on a specific topic.

    Args:
        topic: The research topic to retrieve papers for.
    """
    # TODO(lesson 08): delegate to arxiv_tools.topic_papers_markdown.
    return arxiv_tools.topic_papers_markdown(
        topic=topic,
        paper_dir=PAPER_DIR
    )


@mcp.prompt()
def generate_search_prompt(topic: str, num_papers: int = 5) -> str:
    """Generate a prompt for Claude to find and discuss academic papers."""
    # TODO(lesson 08): delegate to arxiv_tools.generate_search_prompt.
    return arxiv_tools.generate_search_prompt(
        topic=topic,
        num_papers=num_papers
    )


@mcp.prompt()
def generate_research_paper_abstract_compilation_prompt(
    topic: str, 
    num_papers: int = 5
) -> str:
    """Generate a prompt for Claude to find research papers and compile their summaries as Markdowns."""
    # TODO(lesson 08): delegate to arxiv_tools.generate_search_prompt.
    return (
        f"As my content assistant, use the search_papers tool to find {num_papers} papers on '{topic}'.\n"
        f"For each paper:\n"
        "  - Extract its metadata with the extract_info tool and infer its abstract URL.\n"
        "  - Then fetch its abstract HTML page as Markdown.\n"
        "  - Finally, compile it as a document under topic folder directory.\n"
        "After it's done, give me an overview of your compiled results."
    )


def main(transport: str = "stdio") -> None:
    """Run the server. ``transport`` is ``stdio`` or ``streamable-http``."""
    # TODO(lesson 10): call mcp.run(transport=transport).
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
