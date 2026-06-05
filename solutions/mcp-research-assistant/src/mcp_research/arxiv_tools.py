"""Pure research logic for the arXiv MCP server.

This module is deliberately decoupled from MCP and from the ``arxiv`` package:

* It contains **no top-level third-party imports**. The ``arxiv`` package is
  imported *lazily*, inside ``search_papers``, and only when no client has been
  injected. This keeps the module importable (and unit-testable) in a vanilla
  environment that has nothing but the standard library + pytest installed.
* Both functions take a ``paper_dir`` so tests can point them at a temp dir, and
  ``search_papers`` accepts an injected ``client`` (and optional ``search_factory``)
  so the network call can be faked entirely.

The MCP server (``server.py``) is a thin wrapper around these functions; this is
the gradeable core.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Protocol

PAPER_DIR = "papers"


def _topic_slug(topic: str) -> str:
    """Normalize a topic into a filesystem-safe directory name."""
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
            paper objects. Each paper must expose ``get_short_id()``, ``title``,
            ``authors`` (each with ``.name``), ``summary``, ``pdf_url``, and
            ``published`` (with ``.date()``). If ``None``, a real
            ``arxiv.Client()`` is built lazily.
        search_factory: Callable used to build the search query object passed to
            ``client.results``. If ``None``, ``arxiv.Search`` is used lazily.
            Injecting this (with ``client``) avoids importing ``arxiv`` at all.
        paper_dir: Root directory for stored paper metadata.

    Returns:
        The list of arXiv short ids that were found and stored.
    """
    if client is None or search_factory is None:
        # Lazy import: only reached when a dependency was NOT injected. Tests
        # that inject both ``client`` and ``search_factory`` never touch arxiv.
        import arxiv  # noqa: PLC0415  (intentional lazy import)

        if client is None:
            client = arxiv.Client()
        if search_factory is None:
            def search_factory(**kwargs: Any) -> Any:
                return arxiv.Search(
                    sort_by=arxiv.SortCriterion.Relevance, **kwargs
                )

    search = search_factory(query=topic, max_results=max_results)
    papers = client.results(search)

    path = os.path.join(paper_dir, _topic_slug(topic))
    os.makedirs(path, exist_ok=True)
    file_path = os.path.join(path, "papers_info.json")

    try:
        with open(file_path, "r", encoding="utf-8") as json_file:
            papers_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        papers_info = {}

    paper_ids: list[str] = []
    for paper in papers:
        paper_id = paper.get_short_id()
        paper_ids.append(paper_id)
        papers_info[paper_id] = {
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "summary": paper.summary,
            "pdf_url": paper.pdf_url,
            "published": str(paper.published.date()),
        }

    with open(file_path, "w", encoding="utf-8") as json_file:
        json.dump(papers_info, json_file, indent=2)

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
    if not os.path.isdir(paper_dir):
        return f"There's no saved information related to paper {paper_id}."

    for item in os.listdir(paper_dir):
        item_path = os.path.join(paper_dir, item)
        if not os.path.isdir(item_path):
            continue
        file_path = os.path.join(item_path, "papers_info.json")
        if not os.path.isfile(file_path):
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as json_file:
                papers_info = json.load(json_file)
        except (FileNotFoundError, json.JSONDecodeError):
            continue
        if paper_id in papers_info:
            return json.dumps(papers_info[paper_id], indent=2)

    return f"There's no saved information related to paper {paper_id}."


def list_topic_folders(*, paper_dir: str = PAPER_DIR) -> list[str]:
    """Return the topic folders that contain a ``papers_info.json`` file."""
    folders: list[str] = []
    if not os.path.isdir(paper_dir):
        return folders
    for topic_dir in sorted(os.listdir(paper_dir)):
        topic_path = os.path.join(paper_dir, topic_dir)
        if os.path.isdir(topic_path) and os.path.isfile(
            os.path.join(topic_path, "papers_info.json")
        ):
            folders.append(topic_dir)
    return folders


def available_folders_markdown(*, paper_dir: str = PAPER_DIR) -> str:
    """Render the available topic folders as a markdown list."""
    folders = list_topic_folders(paper_dir=paper_dir)
    content = "# Available Topics\n\n"
    if folders:
        for folder in folders:
            content += f"- {folder}\n"
        content += f"\nUse @{folders[-1]} to access papers in that topic.\n"
    else:
        content += "No topics found.\n"
    return content


def topic_papers_markdown(topic: str, *, paper_dir: str = PAPER_DIR) -> str:
    """Render detailed markdown for all stored papers on ``topic``."""
    topic_dir = _topic_slug(topic)
    papers_file = os.path.join(paper_dir, topic_dir, "papers_info.json")

    if not os.path.exists(papers_file):
        return (
            f"# No papers found for topic: {topic}\n\n"
            "Try searching for papers on this topic first."
        )

    try:
        with open(papers_file, "r", encoding="utf-8") as f:
            papers_data = json.load(f)
    except json.JSONDecodeError:
        return (
            f"# Error reading papers data for {topic}\n\n"
            "The papers data file is corrupted."
        )

    content = f"# Papers on {topic.replace('_', ' ').title()}\n\n"
    content += f"Total papers: {len(papers_data)}\n\n"
    for paper_id, paper_info in papers_data.items():
        content += f"## {paper_info['title']}\n"
        content += f"- **Paper ID**: {paper_id}\n"
        content += f"- **Authors**: {', '.join(paper_info['authors'])}\n"
        content += f"- **Published**: {paper_info['published']}\n"
        content += (
            f"- **PDF URL**: [{paper_info['pdf_url']}]({paper_info['pdf_url']})\n\n"
        )
        content += f"### Summary\n{paper_info['summary'][:500]}...\n\n"
        content += "---\n\n"
    return content


def generate_search_prompt(topic: str, num_papers: int = 5) -> str:
    """Build the user-facing prompt that drives a paper search + synthesis."""
    return f"""Search for {num_papers} academic papers about '{topic}' using the search_papers tool.

Follow these instructions:
1. First, search for papers using search_papers(topic='{topic}', max_results={num_papers})
2. For each paper found, extract and organize the following information:
   - Paper title
   - Authors
   - Publication date
   - Brief summary of the key findings
   - Main contributions or innovations
   - Methodologies used
   - Relevance to the topic '{topic}'

3. Provide a comprehensive summary that includes:
   - Overview of the current state of research in '{topic}'
   - Common themes and trends across the papers
   - Key research gaps or areas for future investigation
   - Most impactful or influential papers in this area

4. Organize your findings in a clear, structured format with headings and bullet points for easy readability.

Please present both detailed information about each paper and a high-level synthesis of the research landscape in {topic}."""
