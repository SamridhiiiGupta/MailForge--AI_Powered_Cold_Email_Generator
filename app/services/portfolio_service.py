"""
Portfolio service: loads a CSV of (Techstack, Links) pairs and matches
portfolio items to a set of required job skills.

Strategy: keyword matching (fast, dependency-free, deterministic).
This is intentionally simple — if you need semantic search, swap in
a ChromaDB collection here without changing any calling code.
"""

import os
from typing import Optional

import pandas as pd

from app.config import MAX_PORTFOLIO_LINKS, PORTFOLIO_FILE
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PortfolioService:
    """Loads and queries a portfolio CSV for relevant project links."""

    def __init__(self, csv_path: Optional[str] = None) -> None:
        self._path = csv_path or PORTFOLIO_FILE
        self._data: list[dict] = []

    # ── Loading ───────────────────────────────────────────────────────────────

    def load(self) -> None:
        """
        Read portfolio CSV into memory.
        Safe to call multiple times — skips reload if already loaded.

        CSV schema:
            Techstack  : comma-separated technologies (e.g. "Python, Django, MySQL")
            Links      : URL to the portfolio project
        """
        if self._data:
            return

        if not os.path.exists(self._path):
            logger.error("Portfolio file not found | path=%s", self._path)
            raise FileNotFoundError(
                f"Portfolio CSV not found at '{self._path}'. "
                "Check PORTFOLIO_FILE in your .env or place a CSV at that path."
            )

        df = pd.read_csv(self._path)

        required_cols = {"Techstack", "Links"}
        if not required_cols.issubset(df.columns):
            raise ValueError(
                f"Portfolio CSV must have columns: {required_cols}. "
                f"Found: {set(df.columns)}"
            )

        self._data = df[["Techstack", "Links"]].dropna().to_dict(orient="records")
        logger.info("Portfolio loaded | entries=%d | path=%s", len(self._data), self._path)

    # ── Querying ──────────────────────────────────────────────────────────────

    def query_links(
        self,
        skills: list[str],
        override_links: Optional[list[str]] = None,
    ) -> list[str]:
        """
        Return relevant portfolio links for a set of required skills.

        If override_links are provided (user-configured), they take priority
        over the CSV-based matching and are returned directly (filtered to valid).

        Args:
            skills: Job skill keywords to match against the portfolio techstack.
            override_links: Optional user-supplied links that bypass matching.

        Returns:
            Up to MAX_PORTFOLIO_LINKS relevant URLs.
        """
        # User overrides always win
        if override_links:
            valid = [lnk.strip() for lnk in override_links if lnk.strip()]
            if valid:
                logger.debug("Using override links | count=%d", len(valid))
                return valid[:MAX_PORTFOLIO_LINKS]

        self.load()

        if not skills:
            logger.debug("No skills provided — returning top portfolio items")
            return [row["Links"] for row in self._data[:MAX_PORTFOLIO_LINKS]]

        skill_set = {s.lower().strip() for s in skills}
        matched: list[str] = []

        for row in self._data:
            techstack = row["Techstack"].lower()
            if any(skill in techstack for skill in skill_set):
                matched.append(row["Links"])
            if len(matched) >= MAX_PORTFOLIO_LINKS:
                break

        if not matched:
            logger.debug("No skill matches found — falling back to top portfolio items")
            matched = [row["Links"] for row in self._data[:MAX_PORTFOLIO_LINKS]]

        logger.debug("Portfolio links resolved | count=%d | skills=%s", len(matched), skills)
        return matched
