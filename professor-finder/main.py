"""
AdvisorScout - Main Orchestrator (v2)

Since Google Scholar blocks automated access, this version uses a two-step approach:
1. Uses web search to find professors matching our keywords at target universities
2. Scrapes their profile pages for details
3. Generates a beautiful HTML report + CSV

Run: python main.py
"""

import os
import sys
import io
import re
import json
import logging
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime

from models import Professor, Publication
from config import (
    SEARCH_KEYWORDS, QS_UNIVERSITIES_US, QS_UNIVERSITIES_AUSTRALIA,
    MIN_MATCH_SCORE, REQUEST_DELAY, USER_AGENT, REQUEST_TIMEOUT,
    SCHOLAR_SEARCH_QUERIES, MAX_PUBLICATIONS,
)
from matcher import KeywordMatcher
from output.html_report import generate_html_report
from output.csv_export import export_csv

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("professor_finder.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache.json")
STATUS_FILE = os.path.join(RESULTS_DIR, "status.json")


class ProfessorFinder:
    """Main class that orchestrates the professor discovery pipeline."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        self.all_professors: Dict[str, Professor] = {}
        self._load_cache()
        self.status = {
            "phase": "Starting",
            "total_urls": 0,
            "current_index": 0,
            "current_university": "",
            "professors_total": len(self.all_professors),
            "start_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat()
        }
        self._save_status()

    def _load_cache(self):
        """Load previously found professors from cache."""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for entry in data:
                    prof = Professor(
                        name=entry["name"],
                        university=entry["university"],
                        department=entry.get("department", ""),
                        title=entry.get("title", ""),
                        profile_url=entry.get("profile_url", ""),
                        email=entry.get("email", ""),
                        research_interests=entry.get("research_interests", []),
                        bio=entry.get("bio", ""),
                        scholar_url=entry.get("scholar_url", ""),
                        lab_url=entry.get("lab_url", ""),
                    )
                    for pub_data in entry.get("publications", []):
                        prof.publications.append(Publication(**pub_data))
                    key = f"{prof.name.lower()}|{prof.university.lower()}"
                    self.all_professors[key] = prof
                logger.info(f"Loaded {len(self.all_professors)} professors from cache")
            except Exception as e:
                logger.warning(f"Could not load cache: {e}")

    def _save_cache(self):
        """Save found professors to cache for incremental runs."""
        data = []
        for prof in self.all_professors.values():
            entry = {
                "name": prof.name,
                "university": prof.university,
                "department": prof.department,
                "title": prof.title,
                "profile_url": prof.profile_url,
                "email": prof.email,
                "research_interests": prof.research_interests,
                "bio": prof.bio,
                "scholar_url": prof.scholar_url,
                "lab_url": prof.lab_url,
                "publications": [
                    {"title": p.title, "year": p.year, "authors": p.authors,
                     "venue": p.venue, "url": p.url, "citations": p.citations}
                    for p in prof.publications
                ],
            }
            data.append(entry)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Cache saved: {len(data)} professors")

    def _save_status(self):
        """Save current progress to status.json."""
        os.makedirs(RESULTS_DIR, exist_ok=True)
        self.status["last_update"] = datetime.now().isoformat()
        self.status["professors_total"] = len(self.all_professors)
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.status, f, indent=2)

    def update_status(self, **kwargs):
        """Update status and save to file."""
        self.status.update(kwargs)
        self._save_status()

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page."""
        time.sleep(REQUEST_DELAY)
        try:
            resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "lxml")
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def add_professor(self, prof: Professor):
        """Add a professor (deduplicating by name+university)."""
        key = f"{prof.name.lower()}|{prof.university.lower()}"
        if key in self.all_professors:
            existing = self.all_professors[key]
            # Merge data
            if not existing.email and prof.email:
                existing.email = prof.email
            if not existing.profile_url and prof.profile_url:
                existing.profile_url = prof.profile_url
            if not existing.bio and prof.bio:
                existing.bio = prof.bio
            if prof.research_interests:
                existing_set = set(i.lower() for i in existing.research_interests)
                for interest in prof.research_interests:
                    if interest.lower() not in existing_set:
                        existing.research_interests.append(interest)
        else:
            self.all_professors[key] = prof

    # ── Faculty Page Scrapers ──────────────────────────────────

    def scrape_faculty_page(self, url: str, university: str, department: str) -> List[Professor]:
        """Generic faculty page scraper — tries multiple strategies."""
        soup = self.fetch_page(url)
        if not soup:
            return []

        professors = []

        # Strategy 1: Find profile links
        profile_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            # Skip mailto: links — these are NOT profile links
            if href.lower().startswith("mailto:"):
                continue
            # Look for links that are likely faculty profiles
            if not text or len(text) < 4 or len(text) > 80:
                continue
            # Skip names that look like emails
            if "@" in text:
                continue
            # Skip navigation/menu links
            skip_words = ["home", "about", "contact", "news", "event", "apply",
                         "admission", "research", "program", "course", "degree",
                         "faculty directory", "all faculty", "back", "more",
                         "previous", "next", "search", "login", "menu"]
            if any(w in text.lower() for w in skip_words):
                continue
            # Check if href looks like a profile
            profile_patterns = ["/people/", "/faculty/", "/profile/", "/person/",
                               "/staff/", "/directory/bio", "/user/", "~"]
            if any(p in href.lower() for p in profile_patterns):
                from urllib.parse import urljoin
                full_url = urljoin(url, href)
                profile_links.append((text, full_url))

        # Strategy 2: Look for structured cards
        card_selectors = [
            ".faculty-card", ".person-card", ".staff-card", ".people-card",
            ".views-row", ".faculty-member", ".profile-card", ".team-member",
            'article[class*="person"]', 'div[class*="faculty-"]',
            'div[class*="people-"]', 'li[class*="faculty"]',
        ]
        for sel in card_selectors:
            cards = soup.select(sel)
            if cards and len(cards) >= 3:
                for card in cards:
                    name_el = card.select_one("h2 a, h3 a, h4 a, .name a, .title a")
                    if not name_el:
                        # Skip mailto: links when falling back
                        for a_tag in card.find_all("a", href=True):
                            if not a_tag["href"].lower().startswith("mailto:"):
                                name_el = a_tag
                                break
                    if not name_el:
                        continue
                    name = name_el.get_text(strip=True)
                    if len(name) < 4 or len(name) > 80 or "@" in name:
                        continue
                    from urllib.parse import urljoin
                    href = name_el.get("href", "")
                    if href.lower().startswith("mailto:"):
                        continue
                    link = urljoin(url, href) if href else ""
                    email = self._find_email(card)
                    prof = Professor(
                        name=name, university=university,
                        department=department, profile_url=link, email=email,
                    )
                    professors.append(prof)
                break  # Use first selector that works

        # Use profile links if cards didn't work
        if not professors:
            seen = set()
            for name, link in profile_links:
                if name.lower() not in seen and "@" not in name:
                    seen.add(name.lower())
                    professors.append(Professor(
                        name=name, university=university,
                        department=department, profile_url=link,
                    ))

        logger.info(f"  Found {len(professors)} faculty entries from {university}")
        return professors

    def enrich_professor_profile(self, prof: Professor) -> Professor:
        """Visit a professor's profile page to extract details."""
        if not prof.profile_url:
            return prof

        soup = self.fetch_page(prof.profile_url)
        if not soup:
            return prof

        # Extract email
        if not prof.email:
            prof.email = self._find_email(soup)

        # Extract research interests
        if not prof.research_interests:
            for sel in [".research-interests", ".field-research", ".research-areas",
                       '[class*="interest"]', '[class*="research"]', ".expertise"]:
                el = soup.select_one(sel)
                if el:
                    text = el.get_text(strip=True)
                    if text:
                        prof.research_interests = self._parse_interests(text)
                        break

        # Extract bio
        if not prof.bio:
            for sel in [".biography", ".bio", ".about", ".field-body",
                       ".description", '[class*="biography"]', ".profile-body"]:
                el = soup.select_one(sel)
                if el:
                    prof.bio = el.get_text(strip=True)[:1000]
                    break

            # Fallback: look for long paragraphs that could be a bio
            if not prof.bio:
                for p in soup.find_all("p"):
                    text = p.get_text(strip=True)
                    if len(text) > 200 and any(w in text.lower() for w in
                        ["research", "professor", "phd", "lab", "interests"]):
                        prof.bio = text[:1000]
                        break

        # Extract title
        if not prof.title:
            for sel in [".field-title", ".position", '[class*="title"]',
                       '[class*="position"]', ".job-title"]:
                el = soup.select_one(sel)
                if el:
                    text = el.get_text(strip=True)
                    if any(kw in text.lower() for kw in
                          ["professor", "lecturer", "researcher", "director", "fellow"]):
                        prof.title = text
                        break

        # Find Scholar profile link
        if not prof.scholar_url:
            for a in soup.find_all("a", href=True):
                if "scholar.google" in a["href"]:
                    prof.scholar_url = a["href"]
                    break

        return prof

    @staticmethod
    def _find_email(element) -> str:
        """Find email in an HTML element."""
        for a in element.find_all("a", href=True):
            if "mailto:" in a["href"]:
                return a["href"].replace("mailto:", "").split("?")[0].strip()
        text = element.get_text()
        match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        return match.group(0) if match else ""

    @staticmethod
    def _parse_interests(text: str) -> List[str]:
        """Parse research interests from text."""
        for delim in [";", "|", "\n", ","]:
            if delim in text:
                parts = [p.strip() for p in text.split(delim) if p.strip() and len(p.strip()) > 2]
                if len(parts) > 1:
                    return parts
        return [text] if text and len(text) > 2 else []


# ── Pre-configured University Faculty URLs ──────────────────────
# These are well-known, scrapable faculty directories

FACULTY_URLS = [
    # ═══ US UNIVERSITIES — USER REQUESTED / ACCESSIBLE ═══
    ("University of Toledo", "EECS", "https://www.utoledo.edu/engineering/electrical-engineering-computer-science/faculty/"),
    ("University of Delaware", "ECE", "https://www.ece.udel.edu/people/faculty/"),
    ("University of Illinois Chicago", "ECE", "https://ece.uic.edu/profiles/faculty/"),
    ("University of Houston", "ECE", "https://www.ece.uh.edu/faculty"),
    ("University of Kentucky", "ECE", "https://www.engr.uky.edu/research-faculty/departments/electrical-computer-engineering/faculty"),
    ("University of Miami", "ECE", "https://coe.miami.edu/academics/electrical-computer-engineering/faculty/index.html"),
    ("NJIT", "ECE", "https://ece.njit.edu/faculty"),
    ("Illinois Institute of Technology", "ECE", "https://www.iit.edu/ece/people/faculty"),
    ("University of North Texas", "EE", "https://electrical.engineering.unt.edu/faculty"),
    ("University of South Florida", "EE", "https://www.usf.edu/engineering/ee/people/index.aspx"),
    ("Cleveland State University", "ECE", "https://engineering.csuohio.edu/ece/faculty-and-staff"),
    ("University of Akron", "ECE", "https://www.uakron.edu/engineering/ECE/faculty-staff/"),
    ("Wichita State University", "EECS", "https://www.wichita.edu/academics/engineering/EECS/People/faculty.php"),
    ("University of Memphis", "EE", "https://www.memphis.edu/ee/faculty/index.php"),
    ("Louisiana Tech University", "EE", "https://coes.latech.edu/electrical-engineering/faculty-staff/"),
    ("University of Arkansas", "EECS", "https://electrical-engineering.uark.edu/directory/index.php"),
    ("University of Nevada, Reno", "ECE", "https://www.unr.edu/ece/people"),
    ("University of South Alabama", "ECE", "https://www.southalabama.edu/colleges/engineering/ece/faculty.html"),
    ("North Dakota State University", "ECE", "https://www.ndsu.edu/ece/people/faculty/"),
    ("South Dakota School of Mines", "ECE", "https://www.sdsmt.edu/Academics/Departments/Electrical-Engineering/Faculty-and-Staff/"),
    ("University of Maine", "ECE", "https://ece.umaine.edu/faculty-and-staff/"),
    ("University of Wyoming", "EECS", "https://www.uwyo.edu/eecs/faculty-and-staff/index.html"),
    ("Montana State University", "ECE", "https://www.montana.edu/ece/directory/faculty.html"),
    ("University of Idaho", "ECE", "https://www.uidaho.edu/engr/departments/ece/our-people"),
    ("New Mexico Tech", "EE", "https://www.nmt.edu/academics/ee/faculty.php"),
    ("University of North Dakota", "EE", "https://engineering.und.edu/electrical/faculty/index.html"),
    ("East Carolina University", "ECE", "https://cet.ecu.edu/engineering/electrical-and-computer-engineering/faculty/"),
    ("Old Dominion University", "ECE", "https://www.odu.edu/ece/directory"),
    ("University of Texas at San Antonio", "ECE", "https://engineering.utsa.edu/electrical-computer/faculty/"),
    ("Texas Tech University", "ECE", "https://www.depts.ttu.edu/ece/faculty/"),
    ("University of Alabama at Birmingham", "ECE", "https://www.uab.edu/engineering/ece/people/faculty"),
    ("UA Huntsville", "ECE", "https://www.uah.edu/eng/departments/ece/faculty-staff"),
    ("University of Cincinnati", "ECE", "https://ceas.uc.edu/academics/departments/electrical-computer-engineering/people.html"),
    ("Wright State University", "EE", "https://engineering-computer-science.wright.edu/electrical-engineering/faculty-and-staff"),
    ("University of Massachusetts Lowell", "ECE", "https://www.uml.edu/engineering/electrical-computer/faculty-staff/"),
    ("Rochester Institute of Technology", "ECE", "https://www.rit.edu/engineering/department-electrical-and-microelectronic-engineering"),
    ("University of Central Florida", "ECE", "https://www.ece.ucf.edu/faculty/"),
    ("Florida Institute of Technology", "ECE", "https://www.fit.edu/electrical-computer-engineering/faculty-profiles/"),
    ("University of Rhode Island", "ECBE", "https://web.uri.edu/engineering/meet/ecbe/"),
    ("University of Vermont", "EBE", "https://www.uvm.edu/cems/ee/faculty"),
    ("University of Nebraska-Lincoln", "ECE", "https://engineering.unl.edu/ece/faculty/"),
    ("Oklahoma State University", "ECE", "https://ceat.okstate.edu/ece/faculty.html"),
    ("Kansas State University", "ECE", "https://www.ece.k-state.edu/people/faculty/"),
    ("University of Missouri", "EECS", "https://engineering.missouri.edu/departments/eecs/faculty/"),
    ("Missouri S&T", "ECE", "https://ece.mst.edu/facultyandstaff/"),
    ("UNLV", "ECE", "https://www.unlv.edu/ece/people/faculty"),
    ("Portland State University", "ECE", "https://www.pdx.edu/electrical-computer-engineering/faculty"),
    ("University of Texas at Arlington", "EE", "https://www.uta.edu/academics/schools-colleges/engineering/departments/electrical/people/faculty"),
    ("University of Colorado Denver", "EE", "https://engineering.ucdenver.edu/electrical/faculty-staff"),
    ("Northern Arizona University", "SICCS", "https://nau.edu/siccs/faculty-and-staff/"),
    ("Utah State University", "ECE", "https://ece.usu.edu/people/faculty/index"),

    # ═══ US UNIVERSITIES — QS 400-600 Bracket (Other) ═══
    ("Binghamton University", "ECE", "https://www.binghamton.edu/ece/people/faculty.html"),
    ("Wayne State University", "ECE", "https://engineering.wayne.edu/ece/faculty"),
    ("Florida International University", "ECE", "https://ece.fiu.edu/faculty-and-staff/faculty/"),
    ("George Mason University", "ECE", "https://ece.gmu.edu/faculty-directory/"),
    ("University of New Mexico", "ECE", "https://ece.unm.edu/faculty-staff/index.html"),
    ("Oregon State University", "EECS", "https://eecs.oregonstate.edu/people"),
    ("Florida State University", "ECE", "https://www.eng.famu.fsu.edu/ece/people"),
    ("University at Buffalo", "EE", "https://engineering.buffalo.edu/electrical/people/faculty-directory.html"),
    ("UC Riverside", "ECE", "https://www.ece.ucr.edu/people/faculty"),
    ("UC Santa Cruz", "ECE", "https://engineering.ucsc.edu/departments/electrical-and-computer-engineering/people/"),
    ("Indiana University Bloomington", "ISE", "https://luddy.indiana.edu/contact/faculty/index.html"),
    ("Lehigh University", "ECE", "https://engineering.lehigh.edu/ece/faculty"),
    ("West Virginia University", "LCSEE", "https://lcsee.statler.wvu.edu/faculty-staff/faculty"),
    ("Auburn University", "ECE", "https://www.eng.auburn.edu/ece/faculty-staff/index.html"),
    ("Clarkson University", "ECE", "https://www.clarkson.edu/academics/engineering/electrical-computer-engineering/faculty-staff"),

    # ═══ AUSTRALIAN UNIVERSITIES — QS 300-600 Bracket ═══
    ("Swinburne University", "Engineering", "https://www.swinburne.edu.au/research/centres-groups-clinics/"),
    ("Deakin University", "Engineering", "https://www.deakin.edu.au/school-of-engineering/our-research"),
    ("James Cook University", "Engineering", "https://www.jcu.edu.au/college-of-science-and-engineering/staff"),
    ("University of Newcastle", "Engineering", "https://www.newcastle.edu.au/school/engineering"),
    ("Macquarie University", "Engineering", "https://www.mq.edu.au/faculty-of-science-and-engineering/departments-and-schools/school-of-engineering/our-people"),
    ("Flinders University", "Engineering", "https://www.flinders.edu.au/college-science-engineering/our-people"),
    ("University of Tasmania", "Engineering", "https://www.utas.edu.au/science-engineering-technology/engineering/people"),
    ("La Trobe University", "Engineering", "https://www.latrobe.edu.au/school-computing-engineering-and-mathematical-sciences/staff"),
    ("Western Sydney University", "Engineering", "https://www.westernsydney.edu.au/schools/scem/people/academic_staff"),
    ("University of Canberra", "SIT", "https://www.canberra.edu.au/about-uc/faculties/scitech/staff"),
    ("Murdoch University", "Engineering", "https://www.murdoch.edu.au/school-of-engineering-and-energy/staff"),
    ("University of South Australia", "Engineering", "https://people.unisa.edu.au/"),
    ("Queensland University of Technology", "Engineering", "https://www.qut.edu.au/about/our-people/academic-profiles"),
    ("University of Wollongong", "EIS", "https://www.uow.edu.au/engineering-information-sciences/about-us/our-people/"),
    ("Charles Darwin University", "Engineering", "https://www.cdu.edu.au/science-technology/engineering/staff"),
    ("Edith Cowan University", "Engineering", "https://www.ecu.edu.au/schools/engineering/staff"),
    ("Victoria University", "Engineering", "https://www.vu.edu.au/about-vu/our-teaching-research-staff"),
    ("Charles Sturt University", "Engineering", "https://science-health.csu.edu.au/schools/engineering/staff"),
    ("Southern Cross University", "Engineering", "https://www.scu.edu.au/school-of-engineering-and-technology/our-people/"),
    ("Federation University", "Engineering", "https://federation.edu.au/faculties-and-schools/school-of-science-engineering-and-it/staff-profiles"),
    ("University of New England", "Science/Tech", "https://www.une.edu.au/about-une/faculty-of-science-agriculture-business-and-law/school-of-science-and-technology/staff"),
    ("USC Australia", "Science/Eng", "https://www.usc.edu.au/about/structure/schools/school-of-science-technology-and-engineering/staff"),
]


def main():
    logger.info("=" * 60)
    logger.info("AdvisorScout v2 - Starting")
    logger.info("=" * 60)
    
    finder = ProfessorFinder()
    finder.update_status(phase="Phase 1: Scraping Directories", total_urls=len(FACULTY_URLS))

    # Phase 1: Scrape faculty directories
    logger.info("PHASE 1: Scraping faculty directories...")
    for i, (uni, dept, url) in enumerate(FACULTY_URLS, 1):
        logger.info(f"\n[{i}/{len(FACULTY_URLS)}] Scraping: {uni} - {dept}")
        finder.update_status(current_index=i, current_university=uni)
        try:
            profs = finder.scrape_faculty_page(url, uni, dept)
            for prof in profs:
                finder.add_professor(prof)
            finder._save_cache()
        except Exception as e:
            logger.warning(f"  Failed to scrape {uni}: {e}")

    # Phase 2: Enrich ALL professors
    all_profs = list(finder.all_professors.values())
    finder.update_status(phase="Phase 2: Enriching Profiles", current_index=0, total_urls=len(all_profs))
    
    logger.info("\nPHASE 2: Enriching all professors from profile pages...")
    from concurrent.futures import ThreadPoolExecutor
    
    def enrich_wrapper(prof_tuple):
        idx, prof = prof_tuple
        if not prof.bio and not prof.research_interests and prof.profile_url:
            try:
                finder.enrich_professor_profile(prof)
            except Exception:
                pass
        if idx % 10 == 0:
            finder.update_status(current_index=idx, current_university=prof.name)

    with ThreadPoolExecutor(max_workers=20) as executor:
        list(executor.map(enrich_wrapper, enumerate(all_profs, 1)))

    finder._save_cache()

    # Phase 3: Score and Filter
    finder.update_status(phase="Phase 3: Scoring & Filtering")
    logger.info("\nPHASE 3: Scoring by research interest keywords...")
    matcher = KeywordMatcher()
    scored = matcher.filter_professors(all_profs, min_score=MIN_MATCH_SCORE)

    if not scored:
        scored = matcher.filter_professors(all_profs, min_score=0.3)

    # Phase 4: Output
    finder.update_status(phase="Phase 4: Finalizing Reports")
    logger.info("\nPHASE 4: Generating reports...")
    os.makedirs(RESULTS_DIR, exist_ok=True)

    html_path = os.path.join(RESULTS_DIR, "professors_report.html")
    csv_path = os.path.join(RESULTS_DIR, "professors_data.csv")

    generate_html_report(scored, html_path)
    export_csv(scored, csv_path)

    finder.update_status(phase="Completed", current_index=len(FACULTY_URLS))
    logger.info("\nDONE!")

    try:
        import webbrowser
        webbrowser.open(f"file:///{html_path.replace(os.sep, '/')}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
