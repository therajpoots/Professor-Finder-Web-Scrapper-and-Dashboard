"""
HTML report generator.
Creates a beautiful, self-contained HTML report of found professors with LIVE progress and START button.
"""

import os
import logging
import json
from typing import List, Dict
from datetime import datetime

from models import Professor
from config import get_rank_bracket

logger = logging.getLogger(__name__)


def generate_html_report(professors: List[Professor], output_path: str):
    """Generate a stunning self-contained HTML report with live progress tracking."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Group by university
    by_uni: Dict[str, List[Professor]] = {}
    for p in professors:
        by_uni.setdefault(p.university, []).append(p)

    professor_cards = ""
    for uni, profs in sorted(by_uni.items()):
        bracket = get_rank_bracket(uni)
        country = _get_country(uni)
        
        cards_html = ""
        for p in sorted(profs, key=lambda x: x.match_score, reverse=True):
            pubs_html = ""
            for pub in p.publications[:5]:
                cite = f' <span class="cite">({pub.citations} citations)</span>' if pub.citations else ""
                year = f' <span class="year">{pub.year}</span>' if pub.year else ""
                venue = f' — <em>{pub.venue}</em>' if pub.venue else ""
                link = f'<a href="{pub.url}" target="_blank">' if pub.url else ""
                link_end = "</a>" if pub.url else ""
                pubs_html += f'<li>{link}{_esc(pub.title)}{link_end}{year}{venue}{cite}</li>\n'

            pubs_section = ""
            if pubs_html:
                pubs_section = f'''<div class="section"><h4>📄 Recent Publications</h4><ul class="pubs">{pubs_html}</ul></div>'''

            interests_html = ""
            if p.research_interests:
                tags = "".join(f'<span class="tag">{_esc(i)}</span>' for i in p.research_interests[:12])
                interests_html = f'<div class="tags">{tags}</div>'

            matched_html = ""
            if p.matched_keywords:
                tags = "".join(f'<span class="tag matched">{_esc(k)}</span>' for k in p.matched_keywords[:10])
                matched_html = f'<div class="section"><h4>🎯 Matched Keywords</h4><div class="tags">{tags}</div></div>'

            # Build data attributes for email composer (JSON-safe)
            prof_json_safe = {
                "name": p.name,
                "university": p.university,
                "department": p.department,
                "title": p.title or "Faculty",
                "email": p.email,
                "bio": (p.bio or "")[:1200],
                "interests": ", ".join(p.research_interests[:15]),
                "matched_keywords": ", ".join(p.matched_keywords[:15]),
                "profile_url": p.profile_url,
            }
            prof_json_str = json.dumps(prof_json_safe).replace('"', '&quot;')
            compose_btn = f'<button class="btn compose-btn" data-prof="{prof_json_str}" onclick="openEmailModal(this)">✍️ Compose Email</button>'
            if p.email:
                email_html = f'<a href="mailto:{_esc(p.email)}" class="btn email-btn">📧 {_esc(p.email)}</a> {compose_btn}'
            else:
                email_html = f'<span class="no-email">Email not found</span> {compose_btn}'
            profile_html = f'<a href="{_esc(p.profile_url)}" target="_blank" class="btn profile-btn">🔗 Profile</a>' if p.profile_url else ""
            scholar_html = f'<a href="{_esc(p.scholar_url)}" target="_blank" class="btn scholar-btn">🎓 Scholar</a>' if p.scholar_url else ""

            badge_class = "high" if p.match_score >= 3 else "good" if p.match_score >= 2 else "partial"
            metrics = ""
            if p.h_index or p.citations_total:
                h = f'<span class="metric">h-index: {p.h_index}</span>' if p.h_index else ""
                c = f'<span class="metric">Citations: {p.citations_total:,}</span>' if p.citations_total else ""
                metrics = f'<div class="metrics">{h}{c}</div>'

            bio_html = f'<p class="bio">{_esc(p.bio[:400])}</p>' if p.bio else ""

            cards_html += f'''
<div class="card" data-score="{p.match_score}" data-name="{_esc(p.name.lower())}" data-uni="{_esc(p.university.lower())}" data-interests="{_esc(' '.join(p.research_interests).lower())}" data-country="{country.lower()}">
  <div class="card-header">
    <div><h3 class="prof-name">{_esc(p.name)}</h3>
    <p class="prof-title">{_esc(p.title or 'Faculty')}</p></div>
    <span class="badge {badge_class}">{p.match_level} ({p.match_score})</span>
  </div>
  {metrics}
  {interests_html}
  <div class="actions">{email_html} {profile_html} {scholar_html}</div>
  {matched_html}
  {bio_html}
  {pubs_section}
</div>'''

        professor_cards += f'''
<div class="uni-group" data-country="{country.lower()}">
  <h2 class="uni-name">
    <div class="uni-header-main">
        {_esc(uni)} <span class="count">({len(profs)} professors)</span>
    </div>
    <div class="uni-meta">
        <span class="meta-tag country-tag">{country}</span>
        <span class="meta-tag rank-tag">{bracket}</span>
    </div>
  </h2>
  <div class="cards-grid">{cards_html}</div>
</div>'''

    # Stats
    total = len(professors)
    high = sum(1 for p in professors if p.match_score >= 3)
    good = sum(1 for p in professors if 2 <= p.match_score < 3)
    unis = len(by_uni)
    with_email = sum(1 for p in professors if p.email)
    us_count = sum(1 for p in professors if _get_country(p.university) == "US")
    au_count = sum(1 for p in professors if _get_country(p.university) == "Australia")

    html = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PhD Advisor Dashboard — Live</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:#050508;--surface:#0e0e15;--card:#151525;--border:rgba(255,255,255,0.08);--text:#ffffff;--text2:#a0a0b8;--accent:#7d5fff;--accent2:#b3a4ff;--green:#00d2ad;--orange:#ff9f43;--red:#ff6b6b;--blue:#48dbfb;--glass:rgba(255,255,255,0.03)}}
body{{font-family:'Outfit',sans-serif;background:var(--bg);color:var(--text);line-height:1.6;height:100vh;display:flex;overflow:hidden;}}
.sidebar{{width:340px;height:100vh;background:linear-gradient(180deg,var(--surface) 0%,var(--bg) 100%);border-right:1px solid var(--border);padding:2rem 1.5rem;display:flex;flex-direction:column;overflow-y:auto;flex-shrink:0}}
.main-content{{flex:1;height:100vh;overflow-y:auto;padding:2.5rem;scroll-behavior:smooth;background:radial-gradient(circle at top right, rgba(125,95,255,0.05), transparent 40%)}}

/* Start Button */
.start-box{{margin-bottom:2rem}}
.start-btn{{width:100%;padding:1.2rem;background:linear-gradient(135deg, var(--green), #00b894);border:none;border-radius:16px;color:white;font-weight:700;font-size:1rem;cursor:pointer;transition:all .3s ease;box-shadow:0 8px 25px rgba(0,210,173,0.3);display:flex;align-items:center;justify-content:center;gap:10px}}
.start-btn:hover{{transform:translateY(-3px);box-shadow:0 12px 30px rgba(0,210,173,0.4)}}
.start-btn:active{{transform:translateY(0)}}
.start-btn.running{{background:var(--orange);box-shadow:0 8px 25px rgba(255,159,67,0.3);cursor:wait}}

/* Config Button */
.config-box{{margin-bottom:2rem}}
.config-btn{{width:100%;padding:1rem;background:rgba(255,255,255,0.05);border:1px solid var(--border);border-radius:16px;color:var(--text);font-weight:600;font-size:0.9rem;cursor:pointer;transition:all .3s ease;display:flex;align-items:center;justify-content:center;gap:10px}}
.config-btn:hover{{background:rgba(255,255,255,0.1);border-color:var(--accent)}}

/* Modal Styles */
.modal-overlay{{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);backdrop-filter:blur(10px);display:none;align-items:center;justify-content:center;z-index:1000}}
.modal-content{{background:var(--surface);border:1px solid var(--border);border-radius:24px;width:90%;max-width:800px;max-height:90vh;overflow-y:auto;padding:2.5rem;box-shadow:0 25px 50px rgba(0,0,0,0.5)}}
.modal-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:2rem}}
.modal-header h2{{font-size:1.5rem;background:linear-gradient(135deg,var(--accent2),var(--blue));-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.close-modal{{background:none;border:none;color:var(--text2);font-size:1.5rem;cursor:pointer}}
.kw-group{{margin-bottom:1.5rem;background:var(--glass);padding:1.5rem;border-radius:16px;border:1px solid var(--border)}}
.kw-label{{display:block;font-size:0.8rem;color:var(--accent2);font-weight:700;margin-bottom:0.8rem;text-transform:uppercase;letter-spacing:1px}}
.kw-input{{width:100%;background:var(--bg);border:1px solid var(--border);border-radius:12px;color:var(--text);padding:1rem;font-family:inherit;font-size:0.9rem;min-height:80px;resize:vertical}}
.modal-footer{{display:flex;justify-content:flex-end;gap:1rem;margin-top:2rem;padding-top:1.5rem;border-top:1px solid var(--border)}}
.btn-save{{padding:0.8rem 2rem;background:var(--accent);color:white;border:none;border-radius:12px;font-weight:700;cursor:pointer}}
.btn-cancel{{padding:0.8rem 2rem;background:none;color:var(--text2);border:none;cursor:pointer}}

/* Progress Section */
.live-status{{background:rgba(125,95,255,0.05);border:1px solid rgba(125,95,255,0.2);border-radius:16px;padding:1.2rem;margin-bottom:2rem}}
.status-header{{display:flex;justify-content:space-between;margin-bottom:0.5rem}}
.status-title{{font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--accent2)}}
.status-percent{{font-size:0.8rem;font-weight:700;color:var(--accent2)}}
.progress-bar-bg{{height:8px;background:rgba(255,255,255,0.05);border-radius:4px;overflow:hidden;margin-bottom:0.8rem}}
.progress-bar-fill{{height:100%;background:linear-gradient(90deg, var(--accent), var(--blue));width:0%;transition:width 0.5s ease}}
.status-text{{font-size:0.75rem;color:var(--text2);display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}

.hero h1{{font-size:1.8rem;font-weight:700;background:linear-gradient(135deg,var(--accent2),var(--blue));-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:.5rem;line-height:1.2}}
.hero p{{color:var(--text2);font-size:.85rem;margin-bottom:2rem}}
.stats{{display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;margin-bottom:2rem}}
.stat{{background:var(--glass);border:1px solid var(--border);border-radius:16px;padding:1rem;text-align:center;backdrop-filter:blur(10px)}}
.stat.wide{{grid-column:span 2}}
.stat .num{{font-size:1.6rem;font-weight:700;color:var(--accent2);display:block}}
.stat .label{{font-size:.65rem;color:var(--text2);text-transform:uppercase;letter-spacing:1.5px;font-weight:600}}
.controls{{display:flex;flex-direction:column;gap:0.75rem;margin-bottom:2rem}}
.search-box{{width:100%;padding:0.9rem 1.2rem;background:var(--glass);border:1px solid var(--border);border-radius:12px;color:var(--text);font-size:.9rem;outline:none;transition:all .3s;backdrop-filter:blur(10px)}}
.search-box:focus{{border-color:var(--accent);background:rgba(255,255,255,0.06)}}
.filter-group{{display:flex;flex-direction:column;gap:0.5rem}}
.filter-label{{font-size:.7rem;color:var(--text2);text-transform:uppercase;letter-spacing:1px;margin-bottom:2px;font-weight:700;padding-left:4px}}
.filter-btn{{padding:.75rem 1rem;background:var(--glass);border:1px solid var(--border);border-radius:12px;color:var(--text2);cursor:pointer;font-size:.85rem;transition:all .2s;text-align:left;display:flex;align-items:center;justify-content:space-between;backdrop-filter:blur(10px)}}
.filter-btn:hover{{background:rgba(255,255,255,0.05);color:var(--text)}}
.filter-btn.active{{background:var(--accent);color:white;border-color:var(--accent);box-shadow:0 4px 15px rgba(125,95,255,0.3)}}
.filter-btn .count-badge{{background:rgba(0,0,0,0.2);padding:2px 8px;border-radius:10px;font-size:0.7rem}}
.container{{max-width:1400px;margin:0 auto}}
.uni-group{{margin-bottom:4rem}}
.uni-name{{font-size:1.6rem;font-weight:700;padding:1.2rem 0;border-bottom:1px solid var(--border);position:sticky;top:0;background:rgba(5,5,8,0.85);backdrop-filter:blur(20px);z-index:10;margin-bottom:1.5rem;display:flex;justify-content:space-between;align-items:center}}
.uni-header-main{{display:flex;align-items:center;gap:12px}}
.uni-name .count{{font-size:.85rem;color:var(--text2);font-weight:400}}
.uni-meta{{display:flex;gap:8px}}
.meta-tag{{font-size:0.7rem;padding:4px 10px;border-radius:6px;font-weight:600}}
.country-tag{{background:rgba(72,219,251,0.1);color:var(--blue);border:1px solid rgba(72,219,251,0.2)}}
.rank-tag{{background:rgba(255,159,67,0.1);color:var(--orange);border:1px solid rgba(255,159,67,0.2)}}
.cards-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:1.5rem}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:1.75rem;transition:all .3s ease;display:flex;flex-direction:column;position:relative;overflow:hidden}}
.card::before{{content:'';position:absolute;top:0;left:0;width:4px;height:0;background:var(--accent);transition:height .3s}}
.card:hover{{transform:translateY(-5px);box-shadow:0 12px 40px rgba(0,0,0,0.4);border-color:rgba(125,95,255,0.3)}}
.card:hover::before{{height:100%}}
.card-header{{display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;margin-bottom:1rem}}
.prof-name{{font-size:1.25rem;font-weight:700;letter-spacing:-0.5px}}
.prof-title{{color:var(--text2);font-size:.8rem;margin-top:2px}}
.badge{{padding:.4rem .8rem;border-radius:10px;font-size:.65rem;font-weight:700;white-space:nowrap;flex-shrink:0;text-transform:uppercase;letter-spacing:0.5px}}
.badge.high{{background:rgba(0,210,173,.12);color:var(--green);border:1px solid rgba(0,210,173,.2)}}
.badge.good{{background:rgba(255,159,67,.12);color:var(--orange);border:1px solid rgba(255,159,67,.2)}}
.badge.partial{{background:rgba(72,219,251,.12);color:var(--blue);border:1px solid rgba(72,219,251,.2)}}
.metrics{{display:flex;gap:.6rem;margin-bottom:1rem}}
.metric{{font-size:.7rem;color:var(--accent2);background:rgba(125,95,255,0.1);padding:.3rem .7rem;border-radius:8px;font-weight:600}}
.tags{{display:flex;flex-wrap:wrap;gap:.4rem;margin-bottom:1rem}}
.tag{{font-size:.65rem;padding:.3rem .6rem;background:rgba(255,255,255,0.05);color:var(--text2);border-radius:8px;border:1px solid var(--border)}}
.tag.matched{{background:rgba(0,210,173,.08);color:var(--green);border-color:rgba(0,210,173,.2)}}
.actions{{display:flex;gap:.6rem;flex-wrap:wrap;margin-bottom:1.2rem}}
.btn{{display:inline-flex;align-items:center;gap:.4rem;padding:.5rem .9rem;border-radius:10px;font-size:.75rem;text-decoration:none;transition:all .2s;font-weight:600}}
.email-btn{{background:var(--accent);color:white;box-shadow:0 4px 12px rgba(125,95,255,0.2)}}
.email-btn:hover{{transform:scale(1.02);box-shadow:0 6px 15px rgba(125,95,255,0.3)}}
.profile-btn{{background:rgba(255,255,255,0.05);color:var(--text);border:1px solid var(--border)}}
.profile-btn:hover{{background:rgba(255,255,255,0.1)}}
.scholar-btn{{background:rgba(0,210,173,0.1);color:var(--green);border:1px solid rgba(0,210,173,0.2)}}
.scholar-btn:hover{{background:rgba(0,210,173,0.2)}}
.no-email{{font-size:.75rem;color:var(--text2);font-style:italic;padding:.5rem 0}}
.section{{margin-top:1rem;padding-top:1rem;border-top:1px solid var(--border)}}
.section h4{{font-size:.65rem;color:var(--text2);margin-bottom:.6rem;text-transform:uppercase;letter-spacing:1.5px;font-weight:700}}
.pubs{{list-style:none;padding:0}}
.pubs li{{font-size:.75rem;padding:.5rem 0;border-bottom:1px solid rgba(255,255,255,0.03);color:var(--text2)}}
.pubs li:last-child{{border:none}}
.pubs li a{{color:var(--text);text-decoration:none;font-weight:500}}.pubs li a:hover{{color:var(--accent2);text-decoration:underline}}
.pubs .year{{color:var(--blue);font-weight:700;margin-right:4px}}
.pubs .cite{{color:var(--green);font-size:0.7rem;margin-left:4px}}
.bio{{font-size:.75rem;color:var(--text2);margin-top:.8rem;line-height:1.6;display:-webkit-box;-webkit-box-orient:vertical;overflow:hidden;text-overflow:ellipsis}}
.footer{{margin-top:auto;text-align:center;padding-top:2.5rem;color:var(--text2);font-size:.7rem;opacity:0.6}}
.hidden{{display:none!important}}
::-webkit-scrollbar{{width:8px}}
::-webkit-scrollbar-track{{background:transparent}}
::-webkit-scrollbar-thumb{{background:var(--border);border-radius:10px}}
::-webkit-scrollbar-thumb:hover{{background:rgba(255,255,255,0.15)}}
@media(max-width:900px){{body{{flex-direction:column;overflow:auto}}.sidebar{{width:100%;height:auto;overflow:visible;border-right:none;border-bottom:1px solid var(--border)}}.main-content{{height:auto;overflow:visible;padding:1.5rem}}.cards-grid{{grid-template-columns:1fr}}}}

/* ── Email Compose Modal ── */
.compose-btn{{background:rgba(179,164,255,0.12);color:var(--accent2);border:1px solid rgba(179,164,255,0.25);cursor:pointer;font-family:inherit;}}
.compose-btn:hover{{background:rgba(179,164,255,0.22);transform:scale(1.02);}}
.email-modal-overlay{{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);backdrop-filter:blur(16px);display:none;align-items:center;justify-content:center;z-index:2000;animation:fadeIn .2s ease;}}
.email-modal-overlay.active{{display:flex;}}
@keyframes fadeIn{{from{{opacity:0}}to{{opacity:1}}}}
.email-modal{{background:linear-gradient(145deg,#0e0e18,#13132a);border:1px solid rgba(125,95,255,0.3);border-radius:28px;width:92%;max-width:780px;max-height:92vh;overflow-y:auto;padding:2.5rem;box-shadow:0 30px 80px rgba(0,0,0,0.7),0 0 0 1px rgba(125,95,255,0.1) inset;}}
.email-modal-header{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:2rem;}}
.email-modal-title{{display:flex;flex-direction:column;gap:4px;}}
.email-modal-title h2{{font-size:1.4rem;font-weight:700;background:linear-gradient(135deg,var(--accent2),var(--blue));-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
.email-modal-title .email-to{{font-size:.8rem;color:var(--text2);}}
.email-modal-close{{background:rgba(255,255,255,0.06);border:1px solid var(--border);border-radius:10px;color:var(--text2);font-size:1.2rem;width:36px;height:36px;cursor:pointer;transition:all .2s;display:flex;align-items:center;justify-content:center;}}
.email-modal-close:hover{{background:rgba(255,255,255,0.12);color:var(--text);}}
.email-generating{{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:3rem;gap:1.5rem;}}
.email-spinner{{width:52px;height:52px;border:3px solid rgba(125,95,255,0.15);border-top-color:var(--accent);border-radius:50%;animation:spin .8s linear infinite;}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.email-spinner-text{{color:var(--text2);font-size:.9rem;text-align:center;}}
.email-spinner-text strong{{color:var(--accent2);display:block;margin-bottom:4px;font-size:1rem;}}
.email-form{{display:flex;flex-direction:column;gap:1.2rem;}}
.email-field-label{{font-size:.72rem;color:var(--accent2);font-weight:700;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:.4rem;display:block;}}
.email-subject-input{{width:100%;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:12px;color:var(--text);padding:.9rem 1.1rem;font-family:'Outfit',sans-serif;font-size:.95rem;font-weight:600;outline:none;transition:border-color .2s;}}
.email-subject-input:focus{{border-color:var(--accent);}}
.email-body-input{{width:100%;background:rgba(255,255,255,0.04);border:1px solid var(--border);border-radius:16px;color:var(--text);padding:1.2rem;font-family:'Outfit',sans-serif;font-size:.9rem;line-height:1.75;min-height:280px;resize:vertical;outline:none;transition:border-color .2s;}}
.email-body-input:focus{{border-color:var(--accent);}}
.email-modal-actions{{display:flex;gap:.8rem;flex-wrap:wrap;margin-top:.5rem;padding-top:1.5rem;border-top:1px solid var(--border);}}
.btn-send{{padding:.85rem 2rem;background:linear-gradient(135deg,var(--accent),#6b4de0);color:white;border:none;border-radius:14px;font-weight:700;font-size:.9rem;cursor:pointer;transition:all .25s;box-shadow:0 6px 20px rgba(125,95,255,0.3);font-family:inherit;}}
.btn-send:hover{{transform:translateY(-2px);box-shadow:0 10px 28px rgba(125,95,255,0.45);}}
.btn-send:active{{transform:translateY(0);}}
.btn-copy{{padding:.85rem 1.6rem;background:rgba(0,210,173,0.1);color:var(--green);border:1px solid rgba(0,210,173,0.25);border-radius:14px;font-weight:600;font-size:.9rem;cursor:pointer;transition:all .25s;font-family:inherit;}}
.btn-copy:hover{{background:rgba(0,210,173,0.18);}}
.btn-regenerate{{padding:.85rem 1.4rem;background:rgba(255,255,255,0.05);color:var(--text2);border:1px solid var(--border);border-radius:14px;font-weight:600;font-size:.9rem;cursor:pointer;transition:all .2s;font-family:inherit;margin-left:auto;}}
.btn-regenerate:hover{{background:rgba(255,255,255,0.09);color:var(--text);}}
.email-toast{{position:fixed;bottom:2rem;right:2rem;background:var(--surface);border:1px solid rgba(0,210,173,0.4);border-radius:14px;padding:.9rem 1.4rem;color:var(--green);font-size:.85rem;font-weight:600;z-index:9999;transform:translateY(80px);opacity:0;transition:all .35s cubic-bezier(.34,1.56,.64,1);box-shadow:0 8px 25px rgba(0,0,0,0.4);}}
.email-toast.show{{transform:translateY(0);opacity:1;}}
.email-error{{background:rgba(255,107,107,0.08);border:1px solid rgba(255,107,107,0.25);border-radius:14px;padding:1.2rem 1.5rem;color:#ff9a9a;font-size:.85rem;line-height:1.6;}}
</style></head>
<body>
<div class="sidebar">
  <div class="hero">
    <h1>🎓 PhD Finder</h1>
    <p>Target: 100+ Accessible Universities</p>
  </div>

  <!-- START BUTTON -->
  <div class="start-box">
    <button class="start-btn" id="start-btn">
        🚀 Start New Scan
    </button>
  </div>

  <div class="config-box">
    <button class="config-btn" id="config-btn">
        ⚙️ Configure Keywords
    </button>
  </div>

  <!-- MASS EMAIL BUTTON -->
  <!-- MASS EMAIL BUTTONS -->
  <div class="start-box" style="margin-bottom:1rem; display:flex; gap:0.75rem; flex-wrap:wrap;">
    <button class="start-btn" id="mass-email-btn" style="background:linear-gradient(135deg, var(--accent), #6b4de0); box-shadow:0 8px 25px rgba(125,95,255,0.3); flex:1;">
        📤 Automate Mass Emails
    </button>
    <button class="start-btn" id="stop-campaign-btn" style="background:linear-gradient(135deg,#e05050,#b02020); box-shadow:0 8px 25px rgba(200,50,50,0.3); display:none; flex:1;">
        ⏹ Stop Campaign
    </button>
  </div>

  <!-- CAMPAIGN PROGRESS LINK -->
  <div class="config-box">
    <a href="/campaign" target="_blank" class="config-btn" style="display:flex;align-items:center;justify-content:center;gap:10px;text-decoration:none;">
        📊 Campaign Progress
    </a>
  </div>

  <!-- MASS EMAIL PROGRESS SECTION -->
  <div class="live-status hidden" id="mass-email-status">
    <div class="status-header">
        <span class="status-title" id="mass-status-phase">Email Campaign</span>
        <span class="status-percent" id="mass-status-percent">0/0</span>
    </div>
    <div class="progress-bar-bg">
        <div class="progress-bar-fill" id="mass-status-bar" style="background:linear-gradient(90deg, var(--green), var(--blue));"></div>
    </div>
    <span class="status-text" id="mass-status-prof">Waiting...</span>
  </div>

  <!-- LIVE PROGRESS SECTION -->
  <div class="live-status" id="live-status">
    <div class="status-header">
        <span class="status-title" id="status-phase">Idle</span>
        <span class="status-percent" id="status-percent">0%</span>
    </div>
    <div class="progress-bar-bg">
        <div class="progress-bar-fill" id="status-bar"></div>
    </div>
    <span class="status-text" id="status-uni">Ready to begin</span>
  </div>
  
  <div class="stats">
    <div class="stat wide"><div class="num" id="stat-total">{total}</div><div class="label">Total Professors</div></div>
    <div class="stat"><div class="num" id="stat-unis">{unis}</div><div class="label">Universities</div></div>
    <div class="stat"><div class="num" id="stat-email">{with_email}</div><div class="label">With Email</div></div>
  </div>

  <div class="controls">
    <div class="filter-group">
        <span class="filter-label">Search</span>
        <input type="text" class="search-box" id="search" placeholder="🔍 Name, Interest, University...">
    </div>

    <div class="filter-group">
        <span class="filter-label">Match Level</span>
        <button class="filter-btn active" data-filter="all">🌐 All Matches <span class="count-badge">{total}</span></button>
        <button class="filter-btn" data-filter="high">🔥 High Match <span class="count-badge">{high}</span></button>
        <button class="filter-btn" data-filter="good">⭐ Good Match <span class="count-badge">{good}</span></button>
    </div>

    <div class="filter-group">
        <span class="filter-label">Region</span>
        <button class="filter-btn" data-region="all" id="reg-all">🌍 Worldwide</button>
        <button class="filter-btn" data-region="us" id="reg-us">🇺🇸 United States <span class="count-badge">{us_count}</span></button>
        <button class="filter-btn" data-region="australia" id="reg-au">🇦🇺 Australia <span class="count-badge">{au_count}</span></button>
    </div>
    
    <div class="filter-group">
        <span class="filter-label">Contact</span>
        <button class="filter-btn" data-filter="email">📧 Has Email <span class="count-badge">{with_email}</span></button>
    </div>
  </div>

  <div class="footer">Generated on<br>{datetime.now().strftime("%b %d, %Y at %I:%M %p")}</div>
</div>

<div class="main-content">
  <div class="container" id="report-container">
    {professor_cards}
  </div>
</div>

<!-- EMAIL COMPOSE MODAL -->
<div class="email-modal-overlay" id="email-modal-overlay">
  <div class="email-modal" id="email-modal">
    <div class="email-modal-header">
      <div class="email-modal-title">
        <h2 id="email-modal-prof-name">✍️ Compose Email</h2>
        <span class="email-to" id="email-modal-to">Loading professor...</span>
      </div>
      <button class="email-modal-close" id="email-modal-close" title="Close">✕</button>
    </div>
    <div id="email-modal-body">
      <!-- Content injected by JS -->
    </div>
  </div>
</div>

<!-- TOAST NOTIFICATION -->
<div class="email-toast" id="email-toast">✅ Copied to clipboard!</div>

<!-- CONFIG MODAL -->
<div class="modal-overlay" id="config-modal">
  <div class="modal-content">
    <div class="modal-header">
      <h2>Configure Keywords</h2>
      <button class="close-modal" id="close-modal">&times;</button>
    </div>
    <div id="keywords-container">
        <!-- Dynamic keyword inputs will go here -->
    </div>
    <div class="modal-footer">
      <button class="btn-cancel" id="btn-cancel">Cancel</button>
      <button class="btn-save" id="btn-save">Save Configuration</button>
    </div>
  </div>
</div>

<script>
const search=document.getElementById('search');
const cards=document.querySelectorAll('.card');
const filters=document.querySelectorAll('.filter-btn[data-filter]');
const regionFilters=document.querySelectorAll('.filter-btn[data-region]');
const uniGroups=document.querySelectorAll('.uni-group');
const startBtn = document.getElementById('start-btn');

let activeFilter='all';
let activeRegion='all';

function applyFilters(){{
    const q=search.value.toLowerCase();
    
    cards.forEach(c=>{{
        let show=true;
        const name=c.dataset.name||'';
        const uni=c.dataset.uni||'';
        const int=c.dataset.interests||'';
        const score=parseFloat(c.dataset.score)||0;
        const country=c.dataset.country||'';
        
        if(q && !name.includes(q) && !uni.includes(q) && !int.includes(q)) show=false;
        if(activeFilter==='high' && score<3) show=false;
        if(activeFilter==='good' && score<2) show=false;
        if(activeFilter==='email' && !c.querySelector('.email-btn')) show=false;
        
        if(activeRegion !== 'all' && country !== activeRegion) show=false;
        
        c.classList.toggle('hidden', !show);
    }});
    
    uniGroups.forEach(g=>{{
        const visible=g.querySelectorAll('.card:not(.hidden)');
        const regionMatch = activeRegion === 'all' || g.dataset.country === activeRegion;
        g.classList.toggle('hidden', visible.length===0 || !regionMatch);
    }});
    
    // Update counters
    const visibleCards = document.querySelectorAll('.card:not(.hidden)').length;
    const visibleUnis = document.querySelectorAll('.uni-group:not(.hidden)').length;
    const visibleEmails = document.querySelectorAll('.card:not(.hidden) .email-btn').length;
    
    document.getElementById('stat-total').innerText = visibleCards;
    document.getElementById('stat-unis').innerText = visibleUnis;
    document.getElementById('stat-email').innerText = visibleEmails;
}}

search.addEventListener('input', applyFilters);

filters.forEach(b=>b.addEventListener('click',()=>{{
    filters.forEach(f=>f.classList.remove('active'));
    b.classList.add('active');
    activeFilter=b.dataset.filter;
    applyFilters();
}}));

regionFilters.forEach(b=>b.addEventListener('click',()=>{{
    regionFilters.forEach(f=>f.classList.remove('active'));
    b.classList.add('active');
    activeRegion=b.dataset.region;
    applyFilters();
}}));

// Initialize region filter
document.getElementById('reg-all').classList.add('active');

// START BUTTON HANDLER
startBtn.addEventListener('click', async () => {{
    if (startBtn.classList.contains('running')) return;
    
    if (confirm('Start a fresh scan of all 100+ universities? This may take 10-20 minutes.')) {{
        startBtn.innerText = '⚙️ Scraping in progress...';
        startBtn.classList.add('running');
        try {{
            const response = await fetch('/start');
            const data = await response.json();
            console.log('Scraper started', data);
        }} catch (e) {{
            alert('Failed to start scraper. Make sure app.py is running.');
            startBtn.innerText = '🚀 Start New Scan';
            startBtn.classList.remove('running');
        }}
    }}
}});

// MASS EMAIL BUTTON HANDLER
const massEmailBtn = document.getElementById('mass-email-btn');
const massEmailStatus = document.getElementById('mass-email-status');

massEmailBtn.addEventListener('click', async () => {{
    if (massEmailBtn.classList.contains('running')) return;
    
    if (confirm('Start automating emails to all professors? This will use the DeepSeek AI to compose personalized emails and send them via Gmail SMTP. Emails are sent every 15 seconds.')) {{
        massEmailBtn.innerText = '⚙️ Campaign in progress...';
        massEmailBtn.classList.add('running');
        massEmailStatus.classList.remove('hidden');
        try {{
            const response = await fetch('/start_mass_email');
            const data = await response.json();
            console.log('Mass email started', data);
            stopCampaignBtn.style.display = 'block';
        }} catch (e) {{
            alert('Failed to start mass email. Make sure app.py is running.');
            massEmailBtn.innerText = '📤 Automate Mass Emails';
            massEmailBtn.classList.remove('running');
        }}
    }}
}});

const stopCampaignBtn = document.getElementById('stop-campaign-btn');
stopCampaignBtn.addEventListener('click', async () => {{
    stopCampaignBtn.innerText = '⌛ Stopping...';
    stopCampaignBtn.disabled = true;
    try {{
        await fetch('/stop_mass_email');
    }} catch (e) {{
        console.log('Stop request failed', e);
    }}
}});

// MASS EMAIL POLLING
async function pollMassEmailStatus() {{
    try {{
        const response = await fetch('mass_email_status.json?t=' + new Date().getTime());
        if (response.ok) {{
            const status = await response.json();

            if (status.status === 'idle') return;

            massEmailStatus.classList.remove('hidden');
            document.getElementById('mass-status-prof').innerText = status.current_prof || 'Idle';

            const total = status.total || 0;
            const sent = status.sent || 0;
            const failed = status.failed || 0;
            const percent = total > 0 ? Math.round((sent / total) * 100) : 0;

            document.getElementById('mass-status-percent').innerText = `${{sent}}/${{total}} (${{failed}} failed)`;
            document.getElementById('mass-status-bar').style.width = percent + '%';

            const isRunning = status.status === 'running';
            const isDone = status.status === 'completed';
            const isStopped = status.status === 'stopped';
            const isError = status.status === 'error';

            document.getElementById('mass-status-phase').innerText = status.status.toUpperCase();

            if (isRunning) {{
                massEmailBtn.innerText = '⚙️ Campaign in progress...';
                massEmailBtn.classList.add('running');
                stopCampaignBtn.style.display = 'block';
                stopCampaignBtn.innerText = '⏹ Stop Campaign';
                stopCampaignBtn.disabled = false;
            }} else if (isDone) {{
                massEmailBtn.innerText = '✅ Campaign Complete';
                massEmailBtn.classList.remove('running');
                stopCampaignBtn.style.display = 'none';
            }} else if (isStopped) {{
                massEmailBtn.innerText = '📤 Automate Mass Emails';
                massEmailBtn.classList.remove('running');
                stopCampaignBtn.style.display = 'none';
                stopCampaignBtn.disabled = false;
            }} else if (isError) {{
                massEmailBtn.innerText = '⚠️ Campaign Failed — Retry';
                massEmailBtn.classList.remove('running');
                stopCampaignBtn.style.display = 'none';
            }}
        }}
    }} catch (e) {{
        console.log('Mass email poll failed', e);
    }}
}}

setInterval(pollMassEmailStatus, 3000);
pollMassEmailStatus();

// CONFIG MODAL HANDLER
const configBtn = document.getElementById('config-btn');
const configModal = document.getElementById('config-modal');
const closeModal = document.getElementById('close-modal');
const btnCancel = document.getElementById('btn-cancel');
const btnSave = document.getElementById('btn-save');
const kwContainer = document.getElementById('keywords-container');

configBtn.addEventListener('click', async () => {{
    kwContainer.innerHTML = '<p style="text-align:center;padding:2rem;">Loading keywords...</p>';
    configModal.style.display = 'flex';
    
    try {{
        const response = await fetch('/get_keywords');
        const keywords = await response.json();
        
        kwContainer.innerHTML = '';
        Object.entries(keywords).forEach(([category, list]) => {{
            const group = document.createElement('div');
            group.className = 'kw-group';
            group.innerHTML = `
                <label class="kw-label">${{category.replace(/_/g, ' ')}}</label>
                <textarea class="kw-input" data-category="${{category}}">${{list.join(', ')}}</textarea>
            `;
            kwContainer.appendChild(group);
        }});
    }} catch (e) {{
        kwContainer.innerHTML = '<p style="color:var(--red);text-align:center;padding:2rem;">Failed to load keywords.</p>';
    }}
}});

const hideModal = () => configModal.style.display = 'none';
closeModal.addEventListener('click', hideModal);
btnCancel.addEventListener('click', hideModal);

btnSave.addEventListener('click', async () => {{
    const textareas = kwContainer.querySelectorAll('textarea');
    const newKeywords = {{}};
    
    textareas.forEach(ta => {{
        const category = ta.dataset.category;
        const list = ta.value.split(',').map(s => s.trim()).filter(s => s.length > 0);
        newKeywords[category] = list;
    }});
    
    btnSave.innerText = '⌛ Saving...';
    btnSave.disabled = true;
    
    try {{
        const response = await fetch('/save_keywords', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(newKeywords)
        }});
        if (response.ok) {{
            hideModal();
            alert('Configuration saved! Next scan will use new keywords.');
        }} else {{
            alert('Failed to save configuration.');
        }}
    }} catch (e) {{
        alert('Error saving configuration.');
    }} finally {{
        btnSave.innerText = 'Save Configuration';
        btnSave.disabled = false;
    }}
}});

// LIVE PROGRESS POLLING
async function pollStatus() {{
    try {{
        // Use relative path for status.json since it's served by the same server
        const response = await fetch('status.json?t=' + new Date().getTime());
        if (response.ok) {{
            const status = await response.json();
            
            document.getElementById('status-phase').innerText = status.phase;
            document.getElementById('status-uni').innerText = status.current_university || 'Idle';
            
            const total = status.total_urls || 1;
            const current = status.current_index || 0;
            const percent = Math.round((current / total) * 100);
            
            document.getElementById('status-percent').innerText = percent + '%';
            document.getElementById('status-bar').style.width = percent + '%';
            document.getElementById('stat-total').innerText = status.professors_total;
            
            if (status.phase !== 'Completed' && status.phase !== 'Idle') {{
                startBtn.innerText = '⚙️ Scraping in progress...';
                startBtn.classList.add('running');
            }} else if (status.phase === 'Completed') {{
                startBtn.innerText = '✅ Scan Complete (Click to restart)';
                startBtn.classList.remove('running');
                // Optional: reload after some time
                // location.reload();
            }}
        }}
    }} catch (e) {{
        console.log('Status poll failed', e);
    }}
}}

// Poll every 3 seconds
setInterval(pollStatus, 3000);
pollStatus();

// ── EMAIL COMPOSE MODAL ──────────────────────────────────────
const emailOverlay = document.getElementById('email-modal-overlay');
const emailModalBody = document.getElementById('email-modal-body');
const emailModalClose = document.getElementById('email-modal-close');
const emailModalProfName = document.getElementById('email-modal-prof-name');
const emailModalTo = document.getElementById('email-modal-to');
const emailToast = document.getElementById('email-toast');

let currentProfEmail = '';

function openEmailModal(btn) {{
    const prof = JSON.parse(btn.dataset.prof || '{{}}');
    currentProfEmail = prof.email || '';
    
    emailModalProfName.textContent = '✍️ ' + (prof.name || 'Professor');
    emailModalTo.textContent = prof.email ? 'To: ' + prof.email + ' · ' + prof.university : prof.university || '';
    
    // Show loading state
    emailModalBody.innerHTML = `
        <div class="email-generating">
            <div class="email-spinner"></div>
            <div class="email-spinner-text">
                <strong>Gemini is writing your email...</strong>
                Analyzing ${{prof.name}}'s research profile and crafting a personalized message
            </div>
        </div>
    `;
    
    emailOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    generateEmail(prof);
}}

async function generateEmail(prof) {{
    try {{
        const response = await fetch('/generate_email', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(prof)
        }});
        
        const data = await response.json();
        
        if (data.status === 'error') {{
            showEmailError(data.message);
            return;
        }}
        
        showEmailForm(data.subject, data.body, prof.email);
        
    }} catch (err) {{
        showEmailError('Network error: ' + err.message + '. Make sure app.py is running on port 8000.');
    }}
}}

function showEmailForm(subject, body, toEmail) {{
    emailModalBody.innerHTML = `
        <div class="email-form">
            <div>
                <span class="email-field-label">Subject</span>
                <input type="text" class="email-subject-input" id="email-subject-field" value="${{escHtml(subject)}}">
            </div>
            <div>
                <span class="email-field-label">Email Body — Edit freely before sending</span>
                <textarea class="email-body-input" id="email-body-field">${{escHtml(body)}}</textarea>
            </div>
            <div class="email-modal-actions">
                <button class="btn-send" onclick="sendViaSMTP()" id="btn-send-smtp">📤 Send Now (SMTP)</button>
                <button class="btn-copy" onclick="sendViaMailto()">📧 Open in Email Client</button>
                <button class="btn-copy" onclick="copyEmail()" style="background:rgba(255,255,255,0.06);color:var(--text2);border:1px solid var(--border);">📋 Copy</button>
                <button class="btn-regenerate" onclick="regenerateEmail()">🔄 Regenerate</button>
            </div>
        </div>
    `;
}}

function showEmailError(msg) {{
    emailModalBody.innerHTML = `
        <div class="email-error">
            <strong>⚠️ Could not generate email</strong><br><br>
            ${{msg}}<br><br>
            Make sure the AdvisorScout server (app.py) is running and the DEEPSEEK_API_KEY is set function sendViaMailto() {{
    const subject = encodeURIComponent(document.getElementById('email-subject-field')?.value || '');
    const body = encodeURIComponent(document.getElementById('email-body-field')?.value || '');
    
    // mailto has URL length limits — try to open, fall back to clipboard notice
    const mailtoUrl = `mailto:${{currentProfEmail}}?subject=${{subject}}&body=${{body}}`;
    
    if (mailtoUrl.length > 2000) {{
        // Body too long for mailto — copy instead and open blank mailto
        copyEmail();
        if (currentProfEmail) {{
            window.open(`mailto:${{currentProfEmail}}?subject=${{subject}}`, '_blank');
        }}
        showToast('📋 Body copied! Subject pre-filled in email client.');
    }} else {{
        window.open(mailtoUrl, '_blank');
        showToast('📤 Opened in your email client!');
    }}
}}

function copyEmail() {{
    const subject = document.getElementById('email-subject-field')?.value || '';
    const body = document.getElementById('email-body-field')?.value || '';
    const full = `Subject: ${{subject}}\n\n${{body}}`;
    
    navigator.clipboard.writeText(full).then(() => {{
        showToast('✅ Email copied to clipboard!');
    }}).catch(() => {{
        const ta = document.createElement('textarea');
        ta.value = full;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showToast('✅ Email copied to clipboard!');
    }});
}}

async function sendViaSMTP() {{
    const subject = document.getElementById('email-subject-field')?.value || '';
    const body = document.getElementById('email-body-field')?.value || '';
    const toEmail = currentProfEmail;
    
    if (!toEmail) {{
        showToast('⚠️ No recipient email found for this professor.');
        return;
    }}
    
    const btn = document.getElementById('btn-send-smtp');
    if (btn) {{ btn.textContent = '⌛ Sending...'; btn.disabled = true; }}
    
    try {{
        const res = await fetch('/send_email_now', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ to_email: toEmail, subject: subject, body: body }})
        }});
        const data = await res.json();
        if (data.status === 'sent') {{
            showToast('✅ Email sent to ' + data.to + '!');
            closeEmailModal();
        }} else {{
            showToast('⚠️ Failed: ' + (data.message || 'Unknown error'));
            if (btn) {{ btn.textContent = '📤 Send Now (SMTP)'; btn.disabled = false; }}
        }}
    }} catch (e) {{
        showToast('⚠️ Network error: ' + e.message);
        if (btn) {{ btn.textContent = '📤 Send Now (SMTP)'; btn.disabled = false; }}
    }}
}}
            showToast('⚠️ Failed: ' + (data.message || 'Unknown error'));
            if (btn) { btn.textContent = '📤 Send Now (SMTP)'; btn.disabled = false; }
        }
    } catch (e) {
        showToast('⚠️ Network error: ' + e.message);
    }});
}}

let _lastProfData = null;
function openEmailModal(btn) {{
    const prof = JSON.parse(btn.dataset.prof.replace(/&quot;/g, '"') || '{{}}');
    _lastProfData = prof;
    currentProfEmail = prof.email || '';
    
    emailModalProfName.textContent = '✍️ ' + (prof.name || 'Professor');
    emailModalTo.textContent = prof.email ? 'To: ' + prof.email + ' · ' + prof.university : prof.university || '';
    
    emailModalBody.innerHTML = `
        <div class="email-generating">
            <div class="email-spinner"></div>
            <div class="email-spinner-text">
                <strong>DeepSeek AI is writing your email...</strong>
                Analyzing ${{prof.name}}'s research and crafting a personalized message
            </div>
        </div>
    `;
    
    emailOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    generateEmail(prof);
}}

function regenerateEmail() {{
    if (_lastProfData) {{
        emailModalBody.innerHTML = `
            <div class="email-generating">
                <div class="email-spinner"></div>
                <div class="email-spinner-text">
                    <strong>Generating a fresh version...</strong>
                    Using a slightly different approach
                </div>
            </div>
        `;
        generateEmail(_lastProfData);
    }}
}}

function closeEmailModal() {{
    emailOverlay.classList.remove('active');
    document.body.style.overflow = '';
}}

function showToast(msg) {{
    emailToast.textContent = msg;
    emailToast.classList.add('show');
    setTimeout(() => emailToast.classList.remove('show'), 3000);
}}

function escHtml(str) {{
    if (!str) return '';
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}

emailModalClose.addEventListener('click', closeEmailModal);
emailOverlay.addEventListener('click', (e) => {{ if (e.target === emailOverlay) closeEmailModal(); }});
document.addEventListener('keydown', (e) => {{ if (e.key === 'Escape') closeEmailModal(); }});

</script></body></html>'''

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info(f"HTML report generated: {output_path}")


def _esc(text: str) -> str:
    """Escape HTML special characters."""
    if not text:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


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
