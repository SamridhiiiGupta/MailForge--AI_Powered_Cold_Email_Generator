"""
Tests for app/services/portfolio_service.py

Uses a temporary in-memory CSV to avoid depending on the real portfolio file.
Run with:  pytest tests/ -v
"""

import os
import tempfile

import pandas as pd
import pytest

from app.services.portfolio_service import PortfolioService


@pytest.fixture
def sample_csv(tmp_path):
    """Create a small portfolio CSV for testing."""
    data = {
        "Techstack": [
            "Python, Django, MySQL",
            "React, Node.js, MongoDB",
            "Machine Learning, Python, TensorFlow",
            "Flutter, Firebase, GraphQL",
        ],
        "Links": [
            "https://example.com/python-portfolio",
            "https://example.com/react-portfolio",
            "https://example.com/ml-portfolio",
            "https://example.com/flutter-portfolio",
        ],
    }
    csv_path = tmp_path / "test_portfolio.csv"
    pd.DataFrame(data).to_csv(csv_path, index=False)
    return str(csv_path)


@pytest.fixture
def portfolio(sample_csv):
    svc = PortfolioService(csv_path=sample_csv)
    svc.load()
    return svc


class TestPortfolioServiceLoad:

    def test_loads_successfully(self, portfolio):
        assert len(portfolio._data) == 4

    def test_raises_on_missing_file(self):
        svc = PortfolioService(csv_path="/nonexistent/path/portfolio.csv")
        with pytest.raises(FileNotFoundError):
            svc.load()

    def test_no_double_load(self, portfolio):
        """Calling load() twice should not duplicate data."""
        initial_count = len(portfolio._data)
        portfolio.load()
        assert len(portfolio._data) == initial_count


class TestPortfolioServiceQueryLinks:

    def test_returns_matching_links_for_skills(self, portfolio):
        links = portfolio.query_links(["Python", "Django"])
        assert any("python" in lnk for lnk in links)

    def test_returns_up_to_max_links(self, portfolio):
        links = portfolio.query_links(["Python", "React", "Flutter", "Machine Learning"])
        # MAX_PORTFOLIO_LINKS defaults to 2
        assert len(links) <= 2

    def test_fallback_when_no_skill_match(self, portfolio):
        links = portfolio.query_links(["COBOL", "Fortran"])
        assert len(links) > 0   # Falls back to top items

    def test_override_links_take_priority(self, portfolio):
        overrides = ["https://custom-link1.com", "https://custom-link2.com"]
        links = portfolio.query_links(["Python"], override_links=overrides)
        assert links == overrides

    def test_empty_skills_returns_top_items(self, portfolio):
        links = portfolio.query_links([])
        assert len(links) > 0

    def test_empty_override_list_falls_through_to_matching(self, portfolio):
        """An empty override list should not suppress skill matching."""
        links = portfolio.query_links(["Python"], override_links=[])
        assert any("python" in lnk for lnk in links)
