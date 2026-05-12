"""
Configuration for AdvisorScout.
Contains QS-ranked university lists, search keywords, and scraper settings.
"""

import os
import json

# ============================================================
# SEARCH KEYWORDS — Professors matching these will be collected
# ============================================================

DEFAULT_KEYWORDS = {
    "device_design": [
        "device design", "device fabrication", "mems", "nems",
        "semiconductor", "integrated circuit", "ic design",
        "vlsi", "analog design", "mixed-signal", "rf design",
        "microelectronics", "nanoelectronics", "photonics",
        "sensor design", "transducer", "actuator",
    ],
    "ai_ml": [
        "artificial intelligence", "machine learning",
        "deep learning", "neural network", "computer vision",
        "natural language processing", "reinforcement learning",
        "generative ai", "convolutional neural",
        "federated learning", "ai for health", "ai-driven",
    ],
    "medical_imaging": [
        "medical imaging", "mri", "magnetic resonance",
        "computed tomography", "ct scan", "ultrasound imaging",
        "image processing", "image reconstruction",
        "pet imaging", "x-ray", "fluoroscopy",
        "optical coherence tomography",
        "diffusion tensor", "fmri", "functional imaging",
        "dicom", "radiology", "nuclear medicine",
        "image segmentation", "medical image",
    ],
    "wearables": [
        "wearable", "wearable device", "wearable sensor",
        "health monitoring", "internet of things",
        "fitness tracker", "smartwatch", "biosignal",
        "body area network", "flexible electronics",
        "stretchable electronics", "e-skin", "electronic skin",
        "point of care", "remote patient monitoring",
    ],
    "biomedical": [
        "biomedical", "bioelectronics", "neural interface",
        "biosensor", "bioinstrumentation", "bioimpedance",
        "brain-computer interface", "bci", "neuroprosthetic",
        "implantable", "lab on chip", "microfluidic",
        "tissue engineering", "drug delivery",
        "electrophysiology", "biomedical signal",
    ],
}

# Load keywords from local JSON if exists, otherwise use defaults
KEYWORDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keywords.json")

def load_keywords():
    if os.path.exists(KEYWORDS_FILE):
        try:
            with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_KEYWORDS
    return DEFAULT_KEYWORDS

SEARCH_KEYWORDS = load_keywords()

# ============================================================
# SCRAPER SETTINGS
# ============================================================

REQUEST_DELAY = 0.1
SCHOLAR_DELAY = 5.0
MAX_PUBLICATIONS = 5
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 5
ENABLE_SCHOLAR = True

# Minimum match score to include a professor in results
MIN_MATCH_SCORE = 1.0

# ============================================================
# SCHOLAR SEARCH QUERIES
# These are used for the primary Google Scholar keyword searches
# ============================================================

SCHOLAR_SEARCH_QUERIES = [
    "wearable device design",
    "medical imaging AI",
    "wearable biosensor",
    "MEMS biomedical",
    "wearable health monitoring",
    "medical image deep learning",
    "flexible electronics wearable",
    "brain computer interface",
    "neural interface device",
    "biomedical imaging machine learning",
    "implantable device design",
    "ultrasound imaging AI",
    "MRI machine learning",
    "biosensor wearable IoT",
    "point of care diagnostics device",
    "microfluidic device design",
    "EEG wearable",
    "ECG wearable device",
    "medical device design",
    "semiconductor biosensor",
]

# ============================================================
# QS TOP 600 US & AUSTRALIAN UNIVERSITIES (EE/BME/CS relevant)
# Used to filter Google Scholar results to relevant institutions
# ============================================================

QS_UNIVERSITIES_US = [
    "MIT", "Massachusetts Institute of Technology",
    "Stanford University", "Harvard University",
    "California Institute of Technology", "Caltech",
    "University of Chicago", "University of Pennsylvania",
    "Princeton University", "Yale University",
    "Columbia University", "Johns Hopkins University",
    "Duke University", "Northwestern University",
    "University of California, Berkeley", "UC Berkeley",
    "University of California, Los Angeles", "UCLA",
    "University of Michigan", "Carnegie Mellon University",
    "New York University", "NYU",
    "University of California, San Diego", "UCSD",
    "University of Wisconsin-Madison",
    "University of Illinois Urbana-Champaign", "UIUC",
    "University of Texas at Austin", "UT Austin",
    "Georgia Institute of Technology", "Georgia Tech",
    "Purdue University", "University of Washington",
    "University of Southern California", "USC",
    "Rice University", "Boston University",
    "University of Minnesota",
    "University of Maryland, College Park",
    "Pennsylvania State University", "Penn State",
    "Ohio State University",
    "University of California, Davis", "UC Davis",
    "University of California, Santa Barbara", "UCSB",
    "University of California, Irvine", "UC Irvine",
    "University of Florida",
    "University of Virginia",
    "Vanderbilt University",
    "Washington University in St. Louis",
    "Emory University",
    "University of Pittsburgh",
    "University of Rochester",
    "University of Notre Dame",
    "Tufts University",
    "University of Colorado Boulder",
    "Case Western Reserve University",
    "Northeastern University",
    "University of Arizona",
    "Arizona State University",
    "Virginia Tech",
    "University of Utah",
    "University of Iowa",
    "Stony Brook University", "SUNY Stony Brook",
    "Rutgers University",
    "Texas A&M University",
    "University of North Carolina at Chapel Hill",
    "University of Massachusetts Amherst",
    "Michigan State University",
    "University of Connecticut",
    "University of Delaware",
    "University of Cincinnati",
    "Colorado School of Mines",
    "University of Kansas",
    "University of Oregon",
    "Oregon State University",
    "University of Nebraska-Lincoln",
    "Iowa State University",
    "University of Tennessee",
    "North Carolina State University", "NC State",
    "Clemson University",
    "University of South Florida",
    "George Washington University",
    "Georgetown University",
    "University of Alabama",
    "University of Oklahoma",
    "University of New Mexico",
    "Illinois Institute of Technology",
    "Drexel University",
    "Rensselaer Polytechnic Institute", "RPI",
    "Worcester Polytechnic Institute", "WPI",
    "Stevens Institute of Technology",
    "University of Central Florida",
    "Florida State University",
    "University of Houston",
    "University at Buffalo", "SUNY Buffalo",
    "University of California, Riverside", "UC Riverside",
    "University of California, Santa Cruz", "UC Santa Cruz",
    "University of California, Merced",
    "University of Hawaii at Manoa",
    "Indiana University Bloomington",
    "University of Missouri",
    "University of Louisville",
    "University of Kentucky",
    "University of Nevada, Las Vegas",
    "University of Nevada, Reno",
    "Montana State University",
    "Binghamton University",
    "University of Illinois Chicago",
    "Wayne State University",
    "San Diego State University",
    "Florida International University",
    "University of Texas at Dallas",
    "University of Texas at Arlington",
    "University of Texas at San Antonio",
    "George Mason University",
    "Temple University",
    "University of Maryland, Baltimore County",
    "University of New Hampshire",
    "University of Wyoming",
    "University of Idaho",
    "New Jersey Institute of Technology", "NJIT",
    "Missouri University of Science and Technology",
    "University of Tulsa",
    "University of Dayton",
    "Marquette University",
    "Lehigh University",
    "University of Denver",
    "University of San Diego",
    "Santa Clara University",
    "Rochester Institute of Technology", "RIT",
    "University of Arkansas",
    "University of Mississippi",
    "Louisiana State University",
    "University of South Carolina",
    "University of Vermont",
    "University of Maine",
    "Oklahoma State University",
    "Kansas State University",
    "Mississippi State University",
    "West Virginia University",
    "University of Alabama at Birmingham",
    "Old Dominion University",
    "University of Memphis",
    "Portland State University",
    "University of Massachusetts Lowell",
    "Wichita State University",
    "Northern Arizona University",
    "University of Akron",
    "University of Toledo",
    "Wright State University",
    "Clarkson University",
    "South Dakota School of Mines",
    "New Mexico State University",
    "Auburn University",
]

QS_UNIVERSITIES_AUSTRALIA = [
    "University of Melbourne",
    "University of Sydney",
    "University of New South Wales", "UNSW Sydney", "UNSW",
    "Australian National University", "ANU",
    "University of Queensland", "UQ",
    "Monash University",
    "University of Western Australia", "UWA",
    "University of Adelaide",
    "University of Technology Sydney", "UTS",
    "Macquarie University",
    "RMIT University",
    "Curtin University",
    "Queensland University of Technology", "QUT",
    "University of Wollongong",
    "Deakin University",
    "Griffith University",
    "University of Newcastle",
    "La Trobe University",
    "Swinburne University of Technology",
    "James Cook University",
    "Flinders University",
    "University of Tasmania",
    "Western Sydney University",
    "University of South Australia",
    "Charles Darwin University",
    "Edith Cowan University",
    "Murdoch University",
    "University of Canberra",
    "University of Southern Queensland",
    "Central Queensland University",
    "Bond University",
    "Victoria University",
    "Charles Sturt University",
    "Southern Cross University",
    "Federation University Australia",
    "Australian Catholic University",
    "University of New England",
    "University of the Sunshine Coast",
]

# Mapping universities to their QS Rank Brackets (approximate for 2024/2025)
QS_RANK_BRACKETS = {
    # 400-500 Bracket
    "Binghamton University": "QS 400-500",
    "University of South Florida": "QS 400-500",
    "George Washington University": "QS 400-500",
    "Georgetown University": "QS 400-500",
    "University of Alabama": "QS 400-500",
    "University of Oklahoma": "QS 400-500",
    "University of New Mexico": "QS 400-500",
    "Drexel University": "QS 400-500",
    "University of Central Florida": "QS 400-500",
    "Florida State University": "QS 400-500",
    "University of Houston": "QS 400-500",
    "University at Buffalo": "QS 400-500",
    "UC Riverside": "QS 400-500",
    "UC Santa Cruz": "QS 400-500",
    "Indiana University Bloomington": "QS 400-500",
    "University of Missouri": "QS 400-500",
    "University of Illinois Chicago": "QS 400-500",
    "San Diego State University": "QS 400-500",
    "New Jersey Institute of Technology": "QS 400-500",
    "Lehigh University": "QS 400-500",
    "University of Tasmania": "QS 400-500",
    "Swinburne University of Technology": "QS 400-500",
    "La Trobe University": "QS 400-500",
    "University of Delaware": "QS 400-500",
    "University of Miami": "QS 400-500",
    
    # 500-600 Bracket
    "University of Louisville": "QS 500-600",
    "University of Kentucky": "QS 500-600",
    "University of Texas at Dallas": "QS 500-600",
    "University of Texas at Arlington": "QS 500-600",
    "George Mason University": "QS 500-600",
    "Temple University": "QS 500-600",
    "Wayne State University": "QS 500-600",
    "University of Maryland, Baltimore County": "QS 500-600",
    "Missouri S&T": "QS 500-600",
    "University of Arkansas": "QS 500-600",
    "University of Mississippi": "QS 500-600",
    "Louisiana State University": "QS 500-600",
    "University of South Carolina": "QS 500-600",
    "Oklahoma State University": "QS 500-600",
    "Kansas State University": "QS 500-600",
    "Mississippi State University": "QS 500-600",
    "West Virginia University": "QS 500-600",
    "University of Alabama at Birmingham": "QS 500-600",
    "Auburn University": "QS 500-600",
    "Florida International University": "QS 500-600",
    "Flinders University": "QS 500-600",
    "James Cook University": "QS 500-600",
    "Western Sydney University": "QS 500-600",
    "University of Canberra": "QS 500-600",
    "Murdoch University": "QS 500-600",
    "University of South Australia": "QS 500-600",
    "Illinois Institute of Technology": "QS 500-600",
    "Texas Tech University": "QS 500-600",
    "University of Cincinnati": "QS 500-600",
    "University of Nebraska-Lincoln": "QS 500-600",
    "University of Vermont": "QS 500-600",
    
    # Accessible Bracket (QS 600+)
    "University of Toledo": "QS 600-800",
    "University of North Texas": "QS 600-800",
    "Cleveland State University": "QS 600-800",
    "Louisiana Tech University": "QS 600-800",
    "University of South Alabama": "QS 600-800",
    "North Dakota State University": "QS 600-800",
    "University of Maine": "QS 600-800",
    "University of Wyoming": "QS 600-800",
    "Montana State University": "QS 600-800",
    "University of Idaho": "QS 600-800",
    "New Mexico Tech": "QS 600-800",
    "University of North Dakota": "QS 600-800",
    "East Carolina University": "QS 600-800",
    "UA Huntsville": "QS 600-800",
    "University of Massachusetts Lowell": "QS 600-800",
    "Florida Institute of Technology": "QS 600-800",
    "University of Rhode Island": "QS 600-800",
    "UNLV": "QS 600-800",
    "University of Colorado Denver": "QS 600-800",
    "Utah State University": "QS 600-800",
    "University of Akron": "QS 600-800",
    "Wichita State University": "QS 600-800",
    "University of Memphis": "QS 600-800",
    "Wright State University": "QS 600-800",
}

def get_rank_bracket(university: str) -> str:
    """Return the QS rank bracket for a given university."""
    return QS_RANK_BRACKETS.get(university, "Top 400" if university in (QS_UNIVERSITIES_US + QS_UNIVERSITIES_AUSTRALIA) else "Accessible")

# Combined set for quick lookup (lowercased)
ALL_TARGET_UNIVERSITIES = set()
for name in QS_UNIVERSITIES_US + QS_UNIVERSITIES_AUSTRALIA:
    ALL_TARGET_UNIVERSITIES.add(name.lower())
    # Also add key fragments for fuzzy matching
    for word in name.split():
        if len(word) > 4 and word.lower() not in {"university", "institute", "technology", "state", "school"}:
            pass  # We keep the full names only for matching
