"""
Google Scholar integration module.
Uses the `scholarly` library to enrich professor data with publication info.
"""

import logging
import time
from typing import Optional

from models import Professor, Publication
from config import SCHOLAR_DELAY, MAX_PUBLICATIONS, ENABLE_SCHOLAR

logger = logging.getLogger(__name__)

# Track if scholarly is available
_scholarly_available = False
try:
    from scholarly import scholarly as scholar_api
    _scholarly_available = True
except ImportError:
    logger.warning("scholarly library not installed. Google Scholar enrichment disabled.")
    logger.warning("Install with: pip install scholarly")


class ScholarEnricher:
    """Enriches Professor objects with Google Scholar data."""

    def __init__(self):
        self.enabled = ENABLE_SCHOLAR and _scholarly_available
        self._last_request_time = 0
        if not self.enabled:
            if not _scholarly_available:
                logger.warning("ScholarEnricher disabled: scholarly library not available")
            else:
                logger.info("ScholarEnricher disabled by config")

    def _rate_limit(self):
        """Ensure minimum delay between Scholar requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < SCHOLAR_DELAY:
            wait = SCHOLAR_DELAY - elapsed
            logger.debug(f"Scholar rate limit: waiting {wait:.1f}s")
            time.sleep(wait)
        self._last_request_time = time.time()

    def enrich_professor(self, prof: Professor) -> Professor:
        """
        Look up a professor on Google Scholar and add publication data.
        Modifies the professor in-place and returns it.
        """
        if not self.enabled:
            return prof

        logger.info(f"  📚 Scholar lookup: {prof.name} ({prof.university})")
        self._rate_limit()

        try:
            # Search for the author on Google Scholar
            search_query = f"{prof.name} {prof.university}"
            search_results = scholar_api.search_author(search_query)

            author = None
            try:
                author = next(search_results)
            except StopIteration:
                logger.info(f"    No Scholar profile found for {prof.name}")
                return prof

            if author is None:
                return prof

            # Fill in detailed author information
            try:
                author = scholar_api.fill(author)
            except Exception as e:
                logger.warning(f"    Could not fill Scholar profile for {prof.name}: {e}")
                # Continue with partial data

            # Extract Scholar profile URL
            if hasattr(author, 'scholar_id') and author.get('scholar_id'):
                prof.scholar_url = f"https://scholar.google.com/citations?user={author['scholar_id']}"

            # Extract citation metrics
            if hasattr(author, 'citedby') or 'citedby' in (author if isinstance(author, dict) else {}):
                cited = author.get('citedby', 0) if isinstance(author, dict) else getattr(author, 'citedby', 0)
                prof.citations_total = cited

            if hasattr(author, 'hindex') or 'hindex' in (author if isinstance(author, dict) else {}):
                hidx = author.get('hindex', 0) if isinstance(author, dict) else getattr(author, 'hindex', 0)
                prof.h_index = hidx

            # Extract research interests from Scholar if not already populated
            interests = None
            if isinstance(author, dict):
                interests = author.get('interests', [])
            else:
                interests = getattr(author, 'interests', [])

            if interests and not prof.research_interests:
                prof.research_interests = interests
            elif interests:
                # Merge interests
                existing = set(i.lower() for i in prof.research_interests)
                for interest in interests:
                    if interest.lower() not in existing:
                        prof.research_interests.append(interest)

            # Extract recent publications
            publications = None
            if isinstance(author, dict):
                publications = author.get('publications', [])
            else:
                publications = getattr(author, 'publications', [])

            if publications:
                pub_count = 0
                for pub_data in publications[:MAX_PUBLICATIONS]:
                    try:
                        self._rate_limit()
                        # Try to fill publication details
                        try:
                            pub_data = scholar_api.fill(pub_data)
                        except Exception:
                            pass  # Use partial data

                        bib = {}
                        if isinstance(pub_data, dict):
                            bib = pub_data.get('bib', pub_data)
                        else:
                            bib = getattr(pub_data, 'bib', {})

                        pub = Publication(
                            title=bib.get('title', 'Unknown'),
                            year=str(bib.get('pub_year', bib.get('year', ''))),
                            authors=bib.get('author', ''),
                            venue=bib.get('venue', bib.get('journal', bib.get('conference', ''))),
                            url=pub_data.get('pub_url', '') if isinstance(pub_data, dict)
                                else getattr(pub_data, 'pub_url', ''),
                            citations=pub_data.get('num_citations', 0) if isinstance(pub_data, dict)
                                else getattr(pub_data, 'num_citations', 0),
                        )
                        prof.publications.append(pub)
                        pub_count += 1
                    except Exception as e:
                        logger.debug(f"    Could not parse publication: {e}")
                        continue

                logger.info(f"    Found {pub_count} publications for {prof.name}")

        except Exception as e:
            logger.warning(f"    Scholar lookup failed for {prof.name}: {e}")

        return prof

    def search_by_keyword(self, keyword: str, max_results: int = 20) -> list:
        """
        Search Google Scholar for authors matching a keyword.
        Returns a list of (name, affiliation, scholar_id) tuples.
        """
        if not self.enabled:
            return []

        logger.info(f"  🔍 Scholar keyword search: {keyword}")
        self._rate_limit()

        results = []
        try:
            search = scholar_api.search_keyword(keyword)
            for _ in range(max_results):
                try:
                    self._rate_limit()
                    author = next(search)
                    name = ""
                    affiliation = ""
                    scholar_id = ""

                    if isinstance(author, dict):
                        name = author.get('name', '')
                        affiliation = author.get('affiliation', '')
                        scholar_id = author.get('scholar_id', '')
                    else:
                        name = getattr(author, 'name', '')
                        affiliation = getattr(author, 'affiliation', '')
                        scholar_id = getattr(author, 'scholar_id', '')

                    if name:
                        results.append((name, affiliation, scholar_id))
                except StopIteration:
                    break
        except Exception as e:
            logger.warning(f"    Scholar keyword search failed: {e}")

        return results
