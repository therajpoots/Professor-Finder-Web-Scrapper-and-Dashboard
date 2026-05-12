"""
CSV export module.
Exports professor data to a CSV file for easy use in spreadsheets.
"""

import csv
import logging
import os
from typing import List

from models import Professor
from config import get_rank_bracket

logger = logging.getLogger(__name__)


def export_csv(professors: List[Professor], output_path: str):
    """
    Export professor data to a CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = [
        "Name",
        "University",
        "Country",
        "QS Rank Bracket",
        "Department",
        "Title",
        "Email",
        "Profile URL",
        "Research Interests",
        "Match Score",
        "Match Level",
        "Matched Keywords",
        "Google Scholar URL",
        "h-index",
        "Total Citations",
        "Lab URL",
        "Recent Papers",
        "Bio (excerpt)",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for prof in professors:
            # Format publications
            papers = []
            for pub in prof.publications[:5]:
                paper_str = pub.title
                if pub.year:
                    paper_str += f" ({pub.year})"
                if pub.venue:
                    paper_str += f" — {pub.venue}"
                papers.append(paper_str)

            # Determine country and rank
            country = _get_country(prof.university)
            bracket = get_rank_bracket(prof.university)

            writer.writerow({
                "Name": prof.name,
                "University": prof.university,
                "Country": country,
                "QS Rank Bracket": bracket,
                "Department": prof.department,
                "Title": prof.title,
                "Email": prof.email,
                "Profile URL": prof.profile_url,
                "Research Interests": prof.interests_str,
                "Match Score": prof.match_score,
                "Match Level": prof.match_level,
                "Matched Keywords": "; ".join(prof.matched_keywords),
                "Google Scholar URL": prof.scholar_url,
                "h-index": prof.h_index if prof.h_index else "",
                "Total Citations": prof.citations_total if prof.citations_total else "",
                "Lab URL": prof.lab_url,
                "Recent Papers": " | ".join(papers),
                "Bio (excerpt)": prof.bio[:300] if prof.bio else "",
            })

    logger.info(f"CSV exported: {output_path} ({len(professors)} professors)")


def _get_country(university: str) -> str:
    """Determine country based on university name."""
    au_indicators = [
        "australia", "melbourne", "sydney", "unsw", "monash",
        "queensland", "adelaide", "western australia", "anu",
        "macquarie", "curtin", "rmit", "deakin", "griffith",
        "wollongong", "newcastle", "tasmania", "flinders",
        "latrobe", "swinburne", "james cook", "canberra",
        "charles sturt", "southern cross", "edith cowan",
        "murdoch", "charles darwin", "victoria university",
        "bond university", "university of technology sydney", "uts",
    ]
    uni_lower = university.lower()
    for indicator in au_indicators:
        if indicator in uni_lower:
            return "Australia"
    return "US"
