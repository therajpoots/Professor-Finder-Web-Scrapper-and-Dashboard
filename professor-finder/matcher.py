"""
Keyword matching and scoring engine.
Scores professors based on how well their research interests match target keywords.
"""

import re
import logging
from typing import List, Dict, Tuple

from models import Professor
from config import SEARCH_KEYWORDS

logger = logging.getLogger(__name__)


class KeywordMatcher:
    """Matches and scores professors based on research interest keywords."""

    def __init__(self, keyword_groups: Dict[str, List[str]] = None):
        self.keyword_groups = keyword_groups or SEARCH_KEYWORDS
        # Pre-compile patterns for performance
        self._patterns = {}
        for category, keywords in self.keyword_groups.items():
            self._patterns[category] = [
                (kw, re.compile(re.escape(kw.strip()), re.IGNORECASE))
                for kw in keywords
            ]

    def score_professor(self, prof: Professor) -> Professor:
        """
        Score a professor based on keyword matches.
        Updates match_score and matched_keywords in-place.
        """
        # Build the searchable text from all available info
        searchable = self._build_searchable_text(prof)

        total_score = 0.0
        matched_keywords = []
        matched_categories = set()

        for category, patterns in self._patterns.items():
            category_matched = False
            for keyword, pattern in patterns:
                if pattern.search(searchable):
                    if not category_matched:
                        # Each category match adds 1 point
                        total_score += 1.0
                        category_matched = True
                        matched_categories.add(category)
                    matched_keywords.append(keyword.strip())

            # Bonus for multiple keywords within same category
            category_hits = sum(1 for _, p in patterns if p.search(searchable))
            if category_hits > 1:
                total_score += 0.2 * (category_hits - 1)

        # Bonus for matching across multiple categories (interdisciplinary)
        if len(matched_categories) >= 3:
            total_score += 1.0
        elif len(matched_categories) >= 2:
            total_score += 0.5

        prof.match_score = round(total_score, 2)
        prof.matched_keywords = list(set(matched_keywords))  # Deduplicate

        return prof

    def filter_professors(
        self,
        professors: List[Professor],
        min_score: float = 1.0
    ) -> List[Professor]:
        """
        Score and filter professors, keeping only those above min_score.
        Returns sorted list (highest score first).
        """
        scored = [self.score_professor(prof) for prof in professors]
        filtered = [p for p in scored if p.match_score >= min_score]
        filtered.sort(key=lambda p: p.match_score, reverse=True)

        logger.info(
            f"Keyword filter: {len(professors)} professors → "
            f"{len(filtered)} matched (min_score={min_score})"
        )

        return filtered

    def _build_searchable_text(self, prof: Professor) -> str:
        """Build a single searchable string from all professor fields."""
        parts = [
            prof.name,
            prof.department,
            prof.title,
            prof.bio,
            " ".join(prof.research_interests),
        ]
        # Include publication titles
        for pub in prof.publications:
            parts.append(pub.title)
            if pub.venue:
                parts.append(pub.venue)

        return " ".join(p for p in parts if p)

    def get_match_breakdown(self, prof: Professor) -> Dict[str, List[str]]:
        """
        Get a detailed breakdown of which categories and keywords matched.
        Returns dict of {category: [matched_keywords]}.
        """
        searchable = self._build_searchable_text(prof)
        breakdown = {}

        for category, patterns in self._patterns.items():
            matched = []
            for keyword, pattern in patterns:
                if pattern.search(searchable):
                    matched.append(keyword.strip())
            if matched:
                breakdown[category] = matched

        return breakdown
