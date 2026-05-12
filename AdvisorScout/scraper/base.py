"""
Base scraper with shared HTTP request functionality.
Handles rate limiting, retries, and user-agent spoofing.
"""

import time
import logging
import requests
from bs4 import BeautifulSoup
from typing import Optional
from config import USER_AGENT, REQUEST_TIMEOUT, REQUEST_DELAY

logger = logging.getLogger(__name__)


class BaseScraper:
    """Base class providing HTTP request utilities for all scrapers."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })
        self._last_request_time = 0

    def _rate_limit(self, delay: float = REQUEST_DELAY):
        """Ensure minimum delay between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < delay:
            wait = delay - elapsed
            logger.debug(f"Rate limiting: waiting {wait:.1f}s")
            time.sleep(wait)
        self._last_request_time = time.time()

    def fetch_page(self, url: str, delay: float = REQUEST_DELAY) -> Optional[BeautifulSoup]:
        """
        Fetch a web page and return parsed BeautifulSoup object.
        Returns None if the request fails.
        """
        self._rate_limit(delay)
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            return soup

        except requests.exceptions.HTTPError as e:
            logger.warning(f"HTTP error for {url}: {e}")
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error for {url}: {e}")
        except requests.exceptions.Timeout as e:
            logger.warning(f"Timeout for {url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")

        return None

    def fetch_text(self, url: str) -> Optional[str]:
        """Fetch a URL and return raw text content."""
        self._rate_limit()
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning(f"Failed to fetch text from {url}: {e}")
            return None
