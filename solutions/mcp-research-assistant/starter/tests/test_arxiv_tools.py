"""Offline unit tests for the pure research logic.

These tests import ONLY ``mcp_research.arxiv_tools`` (plus pytest and the fakes
in conftest). They must NOT require ``arxiv``, ``mcp``, or ``anthropic`` — the
injected fake client + search factory keep ``arxiv_tools`` from importing arxiv.
"""

from __future__ import annotations

import json
import os

from mcp_research import arxiv_tools

from conftest import FakeArxivClient, fake_search_factory


def _read_info(paper_dir: str, topic: str) -> dict:
    slug = topic.lower().replace(" ", "_")
    path = os.path.join(paper_dir, slug, "papers_info.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_search_papers_returns_ids(tmp_path, fake_client):
    ids = arxiv_tools.search_papers(
        "transformers",
        max_results=5,
        client=fake_client,
        search_factory=fake_search_factory,
        paper_dir=str(tmp_path),
    )
    assert ids == ["2401.00001", "2401.00002", "2401.00003"]


def test_search_papers_passes_query_and_limit(tmp_path, fake_client):
    arxiv_tools.search_papers(
        "Large Language Models",
        max_results=2,
        client=fake_client,
        search_factory=fake_search_factory,
        paper_dir=str(tmp_path),
    )
    assert fake_client.last_search.query == "Large Language Models"
    assert fake_client.last_search.max_results == 2


def test_search_papers_respects_max_results(tmp_path, fake_client):
    ids = arxiv_tools.search_papers(
        "ai",
        max_results=2,
        client=fake_client,
        search_factory=fake_search_factory,
        paper_dir=str(tmp_path),
    )
    assert len(ids) == 2


def test_search_papers_writes_expected_metadata(tmp_path, fake_client):
    arxiv_tools.search_papers(
        "Deep Learning",
        client=fake_client,
        search_factory=fake_search_factory,
        paper_dir=str(tmp_path),
    )
    info = _read_info(str(tmp_path), "Deep Learning")
    entry = info["2401.00001"]
    assert entry["title"] == "Attention Is All You Need Again"
    assert entry["authors"] == ["Ada Lovelace", "Alan Turing"]
    assert entry["pdf_url"] == "https://arxiv.org/pdf/2401.00001"
    assert entry["published"] == "2024-01-01"


def test_search_papers_slugifies_topic(tmp_path, fake_client):
    arxiv_tools.search_papers(
        "Graph Neural Networks",
        client=fake_client,
        search_factory=fake_search_factory,
        paper_dir=str(tmp_path),
    )
    assert os.path.isdir(os.path.join(str(tmp_path), "graph_neural_networks"))


def test_search_papers_merges_existing(tmp_path, sample_papers):
    first = FakeArxivClient(sample_papers[:1])
    second = FakeArxivClient(sample_papers[1:2])
    arxiv_tools.search_papers(
        "merge", client=first, search_factory=fake_search_factory, paper_dir=str(tmp_path)
    )
    arxiv_tools.search_papers(
        "merge", client=second, search_factory=fake_search_factory, paper_dir=str(tmp_path)
    )
    info = _read_info(str(tmp_path), "merge")
    assert set(info.keys()) == {"2401.00001", "2401.00002"}


def test_extract_info_found(tmp_path, fake_client):
    arxiv_tools.search_papers(
        "nlp", client=fake_client, search_factory=fake_search_factory, paper_dir=str(tmp_path)
    )
    result = arxiv_tools.extract_info("2401.00002", paper_dir=str(tmp_path))
    parsed = json.loads(result)
    assert parsed["title"] == "On the Theory of Everything"


def test_extract_info_not_found(tmp_path):
    result = arxiv_tools.extract_info("9999.99999", paper_dir=str(tmp_path))
    assert "no saved information" in result.lower()
    assert "9999.99999" in result


def test_extract_info_missing_dir(tmp_path):
    missing = os.path.join(str(tmp_path), "does_not_exist")
    result = arxiv_tools.extract_info("2401.00001", paper_dir=missing)
    assert "no saved information" in result.lower()


def test_list_topic_folders(tmp_path, fake_client):
    arxiv_tools.search_papers(
        "topic one", client=fake_client, search_factory=fake_search_factory, paper_dir=str(tmp_path)
    )
    arxiv_tools.search_papers(
        "topic two", client=fake_client, search_factory=fake_search_factory, paper_dir=str(tmp_path)
    )
    folders = arxiv_tools.list_topic_folders(paper_dir=str(tmp_path))
    assert folders == ["topic_one", "topic_two"]


def test_list_topic_folders_empty(tmp_path):
    assert arxiv_tools.list_topic_folders(paper_dir=str(tmp_path)) == []


def test_available_folders_markdown_lists_topics(tmp_path, fake_client):
    arxiv_tools.search_papers(
        "robotics", client=fake_client, search_factory=fake_search_factory, paper_dir=str(tmp_path)
    )
    md = arxiv_tools.available_folders_markdown(paper_dir=str(tmp_path))
    assert "# Available Topics" in md
    assert "- robotics" in md


def test_available_folders_markdown_empty(tmp_path):
    md = arxiv_tools.available_folders_markdown(paper_dir=str(tmp_path))
    assert "No topics found." in md


def test_topic_papers_markdown(tmp_path, fake_client):
    arxiv_tools.search_papers(
        "vision", client=fake_client, search_factory=fake_search_factory, paper_dir=str(tmp_path)
    )
    md = arxiv_tools.topic_papers_markdown("vision", paper_dir=str(tmp_path))
    assert "# Papers on Vision" in md
    assert "Total papers: 3" in md
    assert "2401.00001" in md


def test_topic_papers_markdown_missing(tmp_path):
    md = arxiv_tools.topic_papers_markdown("nope", paper_dir=str(tmp_path))
    assert "No papers found for topic: nope" in md


def test_generate_search_prompt_contains_inputs():
    prompt = arxiv_tools.generate_search_prompt("quantum computing", num_papers=3)
    assert "quantum computing" in prompt
    assert "3" in prompt
    assert "search_papers" in prompt
