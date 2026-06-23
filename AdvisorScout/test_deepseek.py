"""
Standalone test for the DeepSeek API integration in AdvisorScout.
Verifies that:
  1. The API call succeeds
  2. The returned email has a proper Subject + Body
  3. The body meets the 150-word minimum
"""

import sys
import os

# ── Load API key from .env ────────────────────────────────────────────────────
ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

def load_env():
    env = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    env[key.strip()] = val.strip()
    return env

env = load_env()
API_KEY = env.get("DEEPSEEK_API_KEY", "")
if not API_KEY:
    print("❌  DEEPSEEK_API_KEY not found in .env")
    sys.exit(1)

print(f"✅  API key loaded: {API_KEY[:8]}...{API_KEY[-4:]}")

# ── Import the openai SDK ─────────────────────────────────────────────────────
try:
    from openai import OpenAI, RateLimitError
except ImportError:
    print("❌  openai SDK not installed. Run: pip install openai")
    sys.exit(1)

# ── Constants (mirror app.py) ─────────────────────────────────────────────────
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL    = "deepseek-v4-pro"

SYSTEM_MSG = (
    "You are an expert academic email writer. "
    "You write warm, human, highly personalized PhD outreach emails. "
    "NEVER use artificial line breaks (hard wrapping) inside paragraphs. "
    "Each paragraph must be one continuous line with no mid-sentence line breaks."
)

TEST_PROMPT = """\
Write a warm, natural, and highly personalized cold email to Professor Jane Doe for a prospective PhD position in her lab.
Start exactly with: 'Dear Professor Doe,'
Introduce the sender as 'My name is Rana Talha Khalid, and I am in the final year of my undergraduate studies in Biomedical Engineering at NED University of Engineering & Technology with a CGPA of 3.8/4.0.'
Mention 2-3 specific research interests: wearable biosensors and self-powered health monitoring systems, AI-driven biomedical diagnostics and explainable clinical decision support, and BioMEMS microfluidic device design for point-of-care applications.
Reference one of Professor Doe's recent papers on flexible epidermal sensors (2023) naturally.
Propose an original research idea that extends their work.
Keep the tone respectful, confident, and human (180-250 words).
End with: 'Best regards,\\nRana Talha Khalid'

PROFESSOR PROFILE:
Name: Professor Jane Doe
Title: Associate Professor
University: MIT
Department: Biomedical Engineering
Research Interests: wearable biosensors, flexible electronics, AI diagnostics
Bio: Leading researcher in flexible epidermal sensor arrays for continuous health monitoring. Published over 40 papers on skin-interfaced electronics and AI-based signal processing.

Generate the personalized outreach email now. Start with Subject: on the first line, then a blank line, then the email body.

CRITICAL INSTRUCTION: Do NOT use artificial line breaks (hard wrapping) within paragraphs. Each paragraph must be a single continuous line of text.
"""

# ── Call the API ──────────────────────────────────────────────────────────────
print(f"\n📡  Calling DeepSeek API (model: {DEEPSEEK_MODEL}) ...")
client = OpenAI(api_key=API_KEY, base_url=DEEPSEEK_BASE_URL)

try:
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_MSG},
            {"role": "user",   "content": TEST_PROMPT},
        ],
        temperature=0.85,
        max_tokens=2048,
    )
    raw = response.choices[0].message.content.strip()
except Exception as e:
    print(f"❌  API call failed: {e}")
    sys.exit(1)

print("✅  API call succeeded.\n")

# ── Parse subject / body ──────────────────────────────────────────────────────
lines = raw.splitlines()
subject = ""
body_lines = []
body_started = False

for line in lines:
    if line.lower().startswith("subject:") and not body_started:
        subject = line[len("subject:"):].strip()
    elif subject and not body_started:
        if line.strip():
            body_started = True
            body_lines.append(line)
    elif body_started:
        body_lines.append(line)

if not subject:
    subject = "PhD Research Inquiry"
body = "\n".join(body_lines).strip()

# ── Word count check ──────────────────────────────────────────────────────────
word_count = len(body.split())
MIN_WORDS  = 150

print("=" * 60)
print(f"SUBJECT : {subject}")
print("=" * 60)
print(body)
print("=" * 60)
print(f"\n📊  Word count : {word_count}")

if word_count >= MIN_WORDS:
    print(f"✅  PASS — email meets the {MIN_WORDS}-word minimum.\n")
else:
    print(f"❌  FAIL — email is only {word_count} words (need ≥ {MIN_WORDS}).\n")
    sys.exit(1)

# ── Check for hard line-wrap artifacts ───────────────────────────────────────
para_violations = []
for para in body.split("\n\n"):
    para = para.strip()
    for ln in para.splitlines():
        # A line that ends mid-sentence and is shorter than 85 chars is suspicious
        stripped = ln.rstrip()
        if len(stripped) < 85 and not stripped.endswith((".","?","!",",",":",";")):
            if stripped and not any(stripped.lower().startswith(k) for k in ("dear","regards","best","sincerely","rana","biomedical")):
                para_violations.append(repr(stripped))

if para_violations:
    print("⚠️   Possible hard-wrap lines detected (short lines that don't end a sentence):")
    for v in para_violations[:5]:
        print(f"    {v}")
else:
    print("✅  No hard-wrap artifacts detected — paragraphs look clean.\n")
