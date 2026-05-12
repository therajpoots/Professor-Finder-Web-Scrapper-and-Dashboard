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

            email_html = f'<a href="mailto:{_esc(p.email)}" class="btn email-btn">📧 {_esc(p.email)}</a>' if p.email else '<span class="no-email">Email not found</span>'
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
    <div class="stat"><div class="num">{unis}</div><div class="label">Universities</div></div>
    <div class="stat"><div class="num">{with_email}</div><div class="label">With Email</div></div>
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
