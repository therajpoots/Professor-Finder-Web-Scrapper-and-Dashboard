import os
import json
from models import Professor, Publication
from output.html_report import generate_html_report
from config import MIN_MATCH_SCORE
from matcher import KeywordMatcher

# Defined in main.py usually
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache.json")

def regenerate():
    print("Regenerating HTML report with new UI components...")
    
    if not os.path.exists(CACHE_FILE):
        print(f"Cache file {CACHE_FILE} not found.")
        return

    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    all_professors = []
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
        all_professors.append(prof)

    print(f"Loaded {len(all_professors)} professors from cache.")
    
    matcher = KeywordMatcher()
    scored = matcher.filter_professors(all_professors, min_score=MIN_MATCH_SCORE)
    
    output_path = os.path.join("results", "professors_report.html")
    generate_html_report(scored, output_path)
    print(f"Successfully regenerated: {output_path}")

if __name__ == "__main__":
    regenerate()
