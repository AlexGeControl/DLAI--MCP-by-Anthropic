"""Shared pytest fixtures.

The fakes here let ``tests/test_arxiv_tools.py`` run with NO third-party
packages installed (no ``arxiv``, ``mcp``, or ``anthropic``) — only pytest.
They mimic the attribute surface that ``arxiv_tools.search_papers`` reads off of
real ``arxiv`` result objects.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any

import pytest


@dataclass
class FakeAuthor:
    name: str


@dataclass
class FakeDate:
    _date: datetime.date

    def date(self) -> datetime.date:
        return self._date


@dataclass
class FakePaper:
    short_id: str
    title: str
    authors: list[FakeAuthor]
    summary: str
    pdf_url: str
    published: FakeDate

    def get_short_id(self) -> str:
        return self.short_id


@dataclass
class FakeSearch:
    """Stand-in for ``arxiv.Search`` — just records the query kwargs."""

    query: str = ""
    max_results: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


class FakeArxivClient:
    """Stand-in for ``arxiv.Client``; returns a fixed list of papers."""

    def __init__(self, papers: list[FakePaper]) -> None:
        self._papers = papers
        self.last_search: FakeSearch | None = None

    def results(self, search: FakeSearch) -> list[FakePaper]:
        self.last_search = search
        return list(self._papers[: search.max_results])


def fake_search_factory(**kwargs: Any) -> FakeSearch:
    return FakeSearch(
        query=kwargs.get("query", ""),
        max_results=kwargs.get("max_results", 0),
        extra={k: v for k, v in kwargs.items() if k not in ("query", "max_results")},
    )


@pytest.fixture
def sample_papers() -> list[FakePaper]:
    return [
        FakePaper(
            short_id="2401.00001",
            title="Attention Is All You Need Again",
            authors=[FakeAuthor("Ada Lovelace"), FakeAuthor("Alan Turing")],
            summary="A study of transformers. " * 40,
            pdf_url="https://arxiv.org/pdf/2401.00001",
            published=FakeDate(datetime.date(2024, 1, 1)),
        ),
        FakePaper(
            short_id="2401.00002",
            title="On the Theory of Everything",
            authors=[FakeAuthor("Marie Curie")],
            summary="Short summary.",
            pdf_url="https://arxiv.org/pdf/2401.00002",
            published=FakeDate(datetime.date(2024, 2, 2)),
        ),
        FakePaper(
            short_id="2401.00003",
            title="Quantum Widgets",
            authors=[FakeAuthor("Niels Bohr")],
            summary="Quantum stuff.",
            pdf_url="https://arxiv.org/pdf/2401.00003",
            published=FakeDate(datetime.date(2024, 3, 3)),
        ),
    ]


@pytest.fixture
def fake_client(sample_papers: list[FakePaper]) -> FakeArxivClient:
    return FakeArxivClient(sample_papers)
