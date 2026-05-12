"""
Faculty directory scraper.
Scrapes university faculty pages and extracts professor information.
Uses a flexible, multi-strategy approach to handle varied page structures.
"""

import re
import logging
from typing import List, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag

from models import Professor, UniversityTarget
from scraper.base import BaseScraper

logger = logging.getLogger(__name__)


class FacultyScraper(BaseScraper):
    """Scrapes faculty directory pages from universities."""

    def scrape_university(self, target: UniversityTarget) -> List[Professor]:
        """
        Scrape a single university's faculty directory page.
        Returns a list of Professor objects with basic information.
        """
        logger.info(f"{'='*60}")
        logger.info(f"Scraping: {target.name} — {target.department}")
        logger.info(f"URL: {target.faculty_url}")
        logger.info(f"{'='*60}")

        soup = self.fetch_page(target.faculty_url)
        if soup is None:
            logger.warning(f"Failed to fetch page for {target.name}")
            return []

        professors = []

        # Strategy 1: Try configured CSS selectors
        if target.faculty_card_selector:
            professors = self._scrape_with_selectors(soup, target)

        # Strategy 2: If selectors yielded nothing, try generic extraction
        if not professors:
            logger.info(f"CSS selectors yielded no results for {target.name}, trying generic extraction...")
            professors = self._generic_extract(soup, target)

        # Strategy 3: Try link-based extraction as last resort
        if not professors:
            logger.info(f"Generic extraction failed for {target.name}, trying link-based extraction...")
            professors = self._link_based_extract(soup, target)

        logger.info(f"Found {len(professors)} faculty entries from {target.name}")

        # Try to enrich each professor from their profile page
        enriched = []
        for prof in professors:
            if prof.profile_url:
                enriched_prof = self._enrich_from_profile(prof)
                enriched.append(enriched_prof)
            else:
                enriched.append(prof)

        return enriched

    def _scrape_with_selectors(self, soup: BeautifulSoup, target: UniversityTarget) -> List[Professor]:
        """Attempt to scrape using configured CSS selectors."""
        professors = []

        # Try each selector in the comma-separated list
        cards = []
        for selector in target.faculty_card_selector.split(","):
            selector = selector.strip()
            if selector:
                found = soup.select(selector)
                if found:
                    cards = found
                    logger.info(f"Found {len(cards)} cards with selector '{selector}'")
                    break

        for card in cards:
            prof = self._extract_from_card(card, target)
            if prof and prof.name:
                professors.append(prof)

        return professors

    def _extract_from_card(self, card: Tag, target: UniversityTarget) -> Optional[Professor]:
        """Extract professor data from a single faculty card element."""
        prof = Professor(
            name="",
            university=target.name,
            department=target.department,
        )

        # Extract name
        for selector in target.name_selector.split(","):
            selector = selector.strip()
            if selector:
                el = card.select_one(selector)
                if el:
                    prof.name = self._clean_text(el.get_text())
                    break

        if not prof.name:
            return None

        # Extract profile link
        for selector in target.link_selector.split(","):
            selector = selector.strip()
            if selector:
                el = card.select_one(selector)
                if el and el.get("href"):
                    prof.profile_url = urljoin(target.faculty_url, el["href"])
                    break

        # Extract title
        for selector in target.title_selector.split(","):
            selector = selector.strip()
            if selector:
                el = card.select_one(selector)
                if el:
                    prof.title = self._clean_text(el.get_text())
                    break

        # Extract research interests
        for selector in target.interests_selector.split(","):
            selector = selector.strip()
            if selector:
                el = card.select_one(selector)
                if el:
                    text = self._clean_text(el.get_text())
                    prof.research_interests = self._parse_interests(text)
                    break

        # Try to find email in the card
        prof.email = self._find_email_in_element(card)

        return prof

    def _generic_extract(self, soup: BeautifulSoup, target: UniversityTarget) -> List[Professor]:
        """
        Generic extraction strategy — look for common faculty page patterns.
        This handles pages that don't match configured selectors.
        """
        professors = []

        # Common faculty page selectors used across many university sites
        common_selectors = [
            ".faculty-card", ".person-card", ".staff-card",
            ".people-card", ".directory-card", ".member-card",
            ".views-row", ".faculty-listing", ".person-listing",
            ".faculty-member", ".team-member", ".profile-card",
            'article[class*="person"]', 'article[class*="faculty"]',
            'div[class*="faculty"]', 'div[class*="person"]',
            'div[class*="profile"]', 'li[class*="faculty"]',
        ]

        cards = []
        for selector in common_selectors:
            try:
                found = soup.select(selector)
                if found and len(found) > 2:  # Need at least a few results to be valid
                    cards = found
                    logger.info(f"Generic: found {len(cards)} cards with '{selector}'")
                    break
            except Exception:
                continue

        for card in cards:
            prof = self._extract_generic_card(card, target)
            if prof and prof.name:
                professors.append(prof)

        return professors

    def _extract_generic_card(self, card: Tag, target: UniversityTarget) -> Optional[Professor]:
        """Extract professor data using generic heuristics."""
        prof = Professor(
            name="",
            university=target.name,
            department=target.department,
        )

        # Find the most likely name element (usually the first prominent link or heading)
        name_el = None
        for tag in ["h2 a", "h3 a", "h4 a", "h2", "h3", "h4", ".name a", ".title a"]:
            name_el = card.select_one(tag)
            if name_el:
                break

        if not name_el:
            # Fallback: first link in the card
            name_el = card.find("a")

        if name_el:
            prof.name = self._clean_text(name_el.get_text())
            if name_el.name == "a" and name_el.get("href"):
                prof.profile_url = urljoin(target.faculty_url, name_el["href"])
            elif name_el.find("a"):
                link = name_el.find("a")
                prof.profile_url = urljoin(target.faculty_url, link["href"])

        if not prof.name or len(prof.name) < 3:
            return None

        # Find email
        prof.email = self._find_email_in_element(card)

        # Find research interests text
        full_text = self._clean_text(card.get_text())
        if len(full_text) > len(prof.name) + 20:
            prof.bio = full_text

        return prof

    def _link_based_extract(self, soup: BeautifulSoup, target: UniversityTarget) -> List[Professor]:
        """
        Extract faculty by finding links that look like faculty profile URLs.
        Last resort strategy.
        """
        professors = []
        seen_urls = set()

        # Find all links that look like faculty profiles
        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(target.faculty_url, href)

            # Skip if already seen
            if full_url in seen_urls:
                continue

            # Check if link looks like a faculty profile
            profile_patterns = [
                r"/people/", r"/faculty/", r"/profile/",
                r"/person/", r"/staff/", r"/directory/",
                r"profile\.php", r"faculty-profile",
            ]

            is_profile = any(re.search(pat, href, re.IGNORECASE) for pat in profile_patterns)
            if not is_profile:
                continue

            name = self._clean_text(link.get_text())

            # Validate the name (should look like a person's name)
            if not name or len(name) < 3 or len(name) > 60:
                continue
            if any(skip in name.lower() for skip in [
                "faculty", "directory", "people", "staff",
                "all ", "view ", "more", "back", "home",
                "department", "school", "college",
            ]):
                continue

            seen_urls.add(full_url)
            professors.append(Professor(
                name=name,
                university=target.name,
                department=target.department,
                profile_url=full_url,
            ))

        return professors

    def _enrich_from_profile(self, prof: Professor) -> Professor:
        """Visit a professor's profile page to extract additional details."""
        if not prof.profile_url:
            return prof

        soup = self.fetch_page(prof.profile_url)
        if soup is None:
            return prof

        logger.info(f"  Enriching profile: {prof.name}")

        # Extract email if not already found
        if not prof.email:
            prof.email = self._find_email_in_element(soup)

        # Extract research interests from profile page
        if not prof.research_interests:
            interests_text = ""
            interest_selectors = [
                ".research-interests", ".field-research",
                ".research-areas", '[class*="interest"]',
                '[class*="research"]', ".expertise",
                "#research", "#interests",
            ]
            for selector in interest_selectors:
                el = soup.select_one(selector)
                if el:
                    interests_text = self._clean_text(el.get_text())
                    break

            if interests_text:
                prof.research_interests = self._parse_interests(interests_text)

        # Extract bio/description
        if not prof.bio:
            bio_selectors = [
                ".biography", ".bio", ".about",
                ".field-body", ".description",
                '[class*="biography"]', '[class*="about"]',
                "#biography", "#about",
            ]
            for selector in bio_selectors:
                el = soup.select_one(selector)
                if el:
                    prof.bio = self._clean_text(el.get_text())[:1000]  # Limit bio length
                    break

        # Extract title if not already found
        if not prof.title:
            title_selectors = [
                ".field-title", ".position", ".title",
                '[class*="title"]', '[class*="position"]',
            ]
            for selector in title_selectors:
                el = soup.select_one(selector)
                if el:
                    text = self._clean_text(el.get_text())
                    # Make sure this looks like a job title
                    if any(kw in text.lower() for kw in [
                        "professor", "lecturer", "researcher",
                        "director", "chair", "fellow",
                    ]):
                        prof.title = text
                        break

        # Try to find lab URL
        for link in soup.find_all("a", href=True):
            href = link["href"].lower()
            text = link.get_text().lower()
            if any(kw in href or kw in text for kw in ["lab", "group", "research group"]):
                prof.lab_url = urljoin(prof.profile_url, link["href"])
                break

        return prof

    @staticmethod
    def _find_email_in_element(element) -> str:
        """Find an email address within an HTML element."""
        # Check mailto: links first
        for link in element.find_all("a", href=True):
            href = link["href"]
            if "mailto:" in href:
                email = href.replace("mailto:", "").strip()
                # Remove any query parameters
                email = email.split("?")[0]
                return email

        # Fallback: regex search in text content
        text = element.get_text()
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, text)
        if match:
            return match.group(0)

        return ""

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted text — remove extra whitespace, newlines, etc."""
        if not text:
            return ""
        # Replace newlines and tabs with spaces
        text = re.sub(r'[\n\r\t]+', ' ', text)
        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def _parse_interests(text: str) -> List[str]:
        """Parse a text block into a list of research interests."""
        if not text:
            return []

        # Try splitting by common delimiters
        for delimiter in [";", "|", "•", "·", "\n"]:
            if delimiter in text:
                interests = [i.strip() for i in text.split(delimiter) if i.strip()]
                if len(interests) > 1:
                    return interests

        # Try splitting by comma (but be careful of commas within interest names)
        if "," in text:
            interests = [i.strip() for i in text.split(",") if i.strip()]
            if len(interests) > 1:
                return interests

        # Return as single interest if no good delimiter found
        return [text] if text else []
