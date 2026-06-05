"""Pure research logic for the arXiv MCP server.

This module is deliberately decoupled from MCP and from the ``arxiv`` package:

* It must contain **no top-level third-party imports**. Import the ``arxiv``
  package *lazily*, inside ``search_papers``, and only when no client has been
  injected. This keeps the module importable (and unit-testable) in a vanilla
  environment that has nothing but the standard library + pytest installed.
* Both functions take a ``paper_dir`` so tests can point them at a temp dir, and
  ``search_papers`` accepts an injected ``client`` (and optional ``search_factory``)
  so the network call can be faked entirely.

The MCP server (``server.py``) is a thin wrapper around these functions; this is
the gradeable core. See [[05-creating-an-mcp-server]] and
[[08-adding-prompt-and-resource-features]].
"""

from __future__ import annotations

import logging
import json
import os
from pathlib import Path
from typing import Any, Callable, Protocol


logging.basicConfig(level=logging.DEBUG)


PAPER_DIR = "papers"


def _topic_slug(topic: str) -> str:
    """Normalize a topic into a filesystem-safe directory name."""
    # TODO(lesson 05): lowercase and replace spaces with underscores.
    return topic.lower().replace(" ", "_")


class _SupportsResults(Protocol):
    """Structural type for the arXiv client (real or fake)."""

    def results(self, search: Any) -> Any: ...


def search_papers(
    topic: str,
    max_results: int = 5,
    *,
    client: _SupportsResults | None = None,
    search_factory: Callable[..., Any] | None = None,
    paper_dir: str = PAPER_DIR,
) -> list[str]:
    """Search arXiv for ``topic`` and persist paper metadata to disk.

    Results are stored under ``<paper_dir>/<topic_slug>/papers_info.json`` as a
    mapping of ``paper_id -> {title, authors, summary, pdf_url, published}``.
    Re-running for the same topic merges into the existing file.

    Args:
        topic: The search topic.
        max_results: Maximum number of papers to retrieve.
        client: An object with ``.results(search)`` returning an iterable of
            paper objects. Each paper must expose 
            - ``get_short_id()``, 
            - ``title``,
            - ``authors`` (each with ``.name``), 
            - ``summary``, 
            - ``pdf_url``, and
            - ``published`` (with ``.date()``). 
            If ``None``, a real ``arxiv.Client()`` is built lazily.
        search_factory: Callable used to build the search query object passed to
            ``client.results``. If ``None``, ``arxiv.Search`` is used lazily.
            Injecting this (with ``client``) avoids importing ``arxiv`` at all.
        paper_dir: Root directory for stored paper metadata.

    Returns:
        The list of arXiv short ids that were found and stored.
    """
    # TODO(lesson 05):
    #   1. If client or search_factory is None, LAZILY `import arxiv` (never at
    #      module top!) and build the missing one(s): arxiv.Client() and a
    #      factory wrapping arxiv.Search(sort_by=arxiv.SortCriterion.Relevance, ...).
    #   2. Build the search via search_factory(query=topic, max_results=max_results)
    #      and call client.results(search).
    #   3. Ensure <paper_dir>/<topic_slug>/ exists; load existing papers_info.json
    #      if present (tolerate FileNotFoundError / JSONDecodeError -> {}).
    #   4. For each paper, record title, [author.name ...], summary, pdf_url,
    #      str(published.date()) keyed by get_short_id(); collect the ids.
    #   5. Write the merged dict back as indented JSON and return the id list.

    # 1. Perform lazy import to enable offline grader dependency injection 
    if client is None or search_factory is None:
        #
        # Ref. ArXiv API by Google Gemini. No API token is needed
        #
        #
        # # Construct the default API client
        # client = arxiv.Client()
        #
        # # Search for the 5 most recent articles matching a keyword
        # search = arxiv.Search(
        #     query="quantum",
        #     max_results=5,
        #     sort_by=arxiv.SortCriterion.SubmittedDate
        # )
        #
        # # Iterate over the search results and print titles
        # for paper in client.results(search):
        #     print(paper.title)
        #
        import arxiv

        if client is None:
            # Per doc, no API token is needed here
            client = arxiv.Client(
                # request 5, not 100  → fixes the URL anomaly + cuts load
                page_size=max_results,
                # arXiv's requested politeness gap   
                delay_seconds=4.0,
                # modest; NOT high (high retries worsen 429)       
                num_retries=3,           
            )
        if search_factory is None:
            search_factory = lambda **kwargs: arxiv.Search(
                sort_by=arxiv.SortCriterion.Relevance,
                **kwargs,
            )
    #
    # 2. Build the search query and call client.results
    #
    # 2.a Build the search 
    search = search_factory(
        query=topic,
        max_results=max_results,
    )
    # 2.b Call client.results
    try:
        print("Search with arXiv API...")
        papers = list(client.results(search))
    except arxiv.HTTPError:
        # rate-limited or arXiv hiccup: 
        # return what we can rather than 500-ing the tool
        print("arXiv API error (rate limit or other issue); returning empty results.")
        return []

    #
    # 3. Load existing papers_info.json if present, otherwise start with an empty dict
    #
    # 3.a Ensure <paper_dir>/<topic_slug>/ exists
    topic_dir = os.path.join(paper_dir, _topic_slug(topic))
    os.makedirs(topic_dir, exist_ok=True)
    # 3.b Load existing papers_info.json if present (tolerate FileNotFoundError / JSONDecodeError -> {})
    topic_json = os.path.join(topic_dir, "papers_info.json")
    try:
        with open(topic_json, "rt", encoding="utf-8") as topic_file:
            topic_info = json.load(topic_file)
    except (FileNotFoundError, json.JSONDecodeError):
        topic_info = {}

    #
    # 4. For each paper, record 
    #    - title, 
    #    - authors: [author.name ...], 
    #    - summary, 
    #    - pdf_url,
    #    - published: str(published.date()) 
    #    The above record should be keyed by get_short_id(); collect the ids.
    #
    paper_ids = []
    for paper in papers:
        paper_id = paper.get_short_id()

        topic_info[paper_id] = {
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "summary": paper.summary,
            "pdf_url": paper.pdf_url,
            "published": str(paper.published.date()),
        }

        paper_ids.append(paper_id)
    
    #
    # 5. Write the merged dict back as indented JSON and return the id list.
    #
    with open(topic_json, "wt", encoding="utf-8") as topic_file:
        json.dump(topic_info, topic_file, indent=2)

    return paper_ids


def extract_info(paper_id: str, *, paper_dir: str = PAPER_DIR) -> str:
    """Look up stored metadata for ``paper_id`` across all topic folders.

    Args:
        paper_id: The arXiv short id to look for.
        paper_dir: Root directory holding the topic folders.

    Returns:
        A pretty-printed JSON string of the paper's metadata if found, otherwise
        a human-readable "not found" message.
    """
    # TODO(lesson 05): walk each topic folder's papers_info.json (tolerating
    # missing/corrupt files); 
    # - If paper_id is present, return json.dumps(entry, indent=2). 
    # - Otherwise return f"There's no saved information related to paper {paper_id}."
    for dirpath, _, topic_files in os.walk(paper_dir):
        if "papers_info.json" not in topic_files:
            continue
        
        # This branch will only be executed when we walked into a topic folder
        # in this case, dirnames will be [], and we can concate dirpath with "papers_info.json" to get the full path of the topic json file
        topic_json = os.path.join(dirpath, "papers_info.json")
        try:
            with open(topic_json, "rt", encoding="utf-8") as topic_file:
                topic_info = json.load(topic_file)
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    
        # If paper_id is present, return json.dumps(entry, indent=2).
        if paper_id in topic_info:
            return json.dumps(topic_info[paper_id], indent=2)
    # Otherwise return f"There's no saved information related to paper {paper_id}."
    return f"There's no saved information related to paper {paper_id}."

def list_topic_folders(*, paper_dir: str = PAPER_DIR) -> list[str]:
    """Return the topic folders that contain a ``papers_info.json`` file."""
    # TODO(lesson 08): return sorted topic dirs under paper_dir that contain a
    # papers_info.json (empty list if paper_dir doesn't exist).
    topic_names = []
    for dirpath, _, topic_files in os.walk(paper_dir):
        if "papers_info.json" not in topic_files:
            continue

        topic_names.append(os.path.basename(dirpath))

    return sorted(topic_names)

def available_folders_markdown(*, paper_dir: str = PAPER_DIR) -> str:
    """Render the available topic folders as a markdown list."""
    # TODO(lesson 08): build a "# Available Topics" markdown list from
    # list_topic_folders(); if none, say "No topics found."
    if topic_folders := list_topic_folders(paper_dir=paper_dir):
        md = "# Available Topics\n\n"
        for topic_normalized in topic_folders:
            md += f"- {topic_normalized}\n"
        return md
    else:
        return "# No topics found."

def topic_papers_markdown(topic: str, *, paper_dir: str = PAPER_DIR) -> str:
    """Render detailed markdown for all stored papers on ``topic``."""
    # TODO(lesson 08): if no papers_info.json for the topic slug, return a
    # "# No papers found for topic: {topic}" message. Otherwise build a markdown
    # report: "# Papers on <Title>", "Total papers: N", then per-paper sections.
    topic_json = os.path.join(paper_dir, _topic_slug(topic), "papers_info.json")
    try:
        with open(topic_json, "rt", encoding="utf-8") as topic_file:
            topic_info = json.load(topic_file)
        
        md = f"# Papers on {topic.title()}\n\nTotal papers: {len(topic_info)}"
        # Build per-paper sections
        for paper_id, paper in topic_info.items():  
            md += f"\n\n## {paper['title']} ({paper_id})\n"
            md += f"- Authors: {', '.join(paper['authors'])}\n"
            md += f"- Published: {paper['published']}\n"
            md += f"- Summary: {paper['summary']}\n"
            md += f"- PDF: {paper['pdf_url']}\n"
        
        return md
    except (FileNotFoundError, json.JSONDecodeError):
        return f"# No papers found for topic: {topic}"


def generate_search_prompt(topic: str, num_papers: int = 5) -> str:
    """Build the user-facing prompt that drives a paper search + synthesis."""
    return (
        f"Use the search_papers tool to find {num_papers} papers on '{topic}'.\n"
        f"After retrieving the results, summarize the key findings, themes, and "
        f"contributions across all papers. Highlight any consensus or disagreements "
        f"between authors."
    )


# --------------------------------------------------------------------------- #
# Debug CLI (python-fire) — call the pure functions directly, bypassing the
# FastMCP / Inspector stack so you can probe the arXiv client standalone.
# `fire` is imported LAZILY so this module keeps NO top-level third-party
# imports (the offline unit tests must import arxiv_tools with only the stdlib).
# --------------------------------------------------------------------------- #
def _cli() -> None:
    """Expose the public tools/resources/prompt as a CLI for standalone probing.

    Run from the package dir so the default ``PAPER_DIR='papers'`` resolves:

        python -m mcp_research.arxiv_tools search_papers "diffusion models" --max_results=3
        python -m mcp_research.arxiv_tools extract_info 2006.11239
        python -m mcp_research.arxiv_tools list_topic_folders
        python -m mcp_research.arxiv_tools available_folders_markdown
        python -m mcp_research.arxiv_tools topic_papers_markdown "diffusion models"
        python -m mcp_research.arxiv_tools generate_search_prompt "llm agents" --num_papers=4
    """
    import fire

    fire.Fire(
        {
            "search_papers": search_papers,
            "extract_info": extract_info,
            "list_topic_folders": list_topic_folders,
            "available_folders_markdown": available_folders_markdown,
            "topic_papers_markdown": topic_papers_markdown,
            "generate_search_prompt": generate_search_prompt,
        }
    )


if __name__ == "__main__":
    _cli()
