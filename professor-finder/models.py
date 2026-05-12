"""
Data models for the Professor Finder tool.
Defines the core data structures used throughout the application.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Publication:
    """Represents a single academic publication."""
    title: str
    year: Optional[str] = None
    authors: Optional[str] = None
    venue: Optional[str] = None  # Journal / Conference name
    url: Optional[str] = None
    citations: int = 0

    def __str__(self):
        parts = [self.title]
        if self.authors:
            parts.append(f"  Authors: {self.authors}")
        if self.venue:
            parts.append(f"  Venue: {self.venue}")
        if self.year:
            parts.append(f"  Year: {self.year}")
        return "\n".join(parts)


@dataclass
class Professor:
    """Represents a professor found during scraping."""
    name: str
    university: str
    department: str = ""
    title: str = ""  # e.g., "Associate Professor"
    profile_url: str = ""
    email: str = ""
    research_interests: List[str] = field(default_factory=list)
    bio: str = ""
    publications: List[Publication] = field(default_factory=list)
    scholar_url: str = ""
    lab_url: str = ""
    match_score: float = 0.0
    matched_keywords: List[str] = field(default_factory=list)
    h_index: Optional[int] = None
    citations_total: Optional[int] = None

    @property
    def interests_str(self) -> str:
        """Return research interests as a comma-separated string."""
        return ", ".join(self.research_interests) if self.research_interests else ""

    @property
    def match_level(self) -> str:
        """Return human-readable match level."""
        if self.match_score >= 3:
            return "🔥 High Match"
        elif self.match_score >= 2:
            return "⭐ Good Match"
        elif self.match_score >= 1:
            return "📌 Partial Match"
        return "📎 Low Match"

    def __str__(self):
        return (
            f"{self.name} — {self.title}\n"
            f"  University: {self.university}\n"
            f"  Department: {self.department}\n"
            f"  Email: {self.email}\n"
            f"  Interests: {self.interests_str}\n"
            f"  Match: {self.match_level} (score={self.match_score})"
        )


@dataclass
class UniversityTarget:
    """Configuration for a university scraping target."""
    name: str
    country: str  # "US" or "Australia"
    department: str
    faculty_url: str
    # CSS selectors for scraping
    faculty_card_selector: str = ""
    name_selector: str = ""
    link_selector: str = ""
    title_selector: str = ""
    interests_selector: str = ""
    email_selector: str = ""
    bio_selector: str = ""
    # Whether the page loads dynamically (needs Selenium)
    is_dynamic: bool = False
    # Additional notes
    notes: str = ""
