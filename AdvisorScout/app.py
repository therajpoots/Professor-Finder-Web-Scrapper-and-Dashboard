"""
Web UI Server for AdvisorScout.
Provides a Start Scraping button, serves the dashboard,
and handles AI email generation via DeepSeek API (deepseek-v4-pro).
"""

import http.server
import socketserver
import threading
import json
import os
import subprocess
import sys
import urllib.request
from urllib.parse import urlparse, parse_qs

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
STOP_FLAG_FILE = os.path.join(BASE_DIR, "results", "campaign_stop.flag")
DASHBOARD_PATH = os.path.join(RESULTS_DIR, "professors_report.html")
CV_PATH = os.path.join(BASE_DIR, "Rana_Talha_Khalid_CV__.pdf")
PROMPT_PATH = os.path.join(BASE_DIR, "prompt.txt")
ENV_PATH = os.path.join(BASE_DIR, ".env")


def _is_stop_requested():
    """Check if a stop flag file exists on disk."""
    return os.path.exists(STOP_FLAG_FILE)


def _set_stop_flag():
    """Write the stop flag file to disk."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(STOP_FLAG_FILE, "w") as f:
        f.write("stop")


def _clear_stop_flag():
    """Remove the stop flag file."""
    if os.path.exists(STOP_FLAG_FILE):
        os.remove(STOP_FLAG_FILE)


DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-pro"




def load_env():
    """Load environment variables from .env file."""
    env = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    env[key.strip()] = val.strip()
    return env


def load_cv():
    """Load Rana's CV from PDF."""
    if os.path.exists(CV_PATH):
        try:
            import PyPDF2
            text = ""
            with open(CV_PATH, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            if text.strip():
                return text.strip()
        except Exception as e:
            print(f"Error reading PDF CV: {e}")
            
    # Fallback
    fallback_path = os.path.join(BASE_DIR, "rana_cv.txt")
    if os.path.exists(fallback_path):
        with open(fallback_path, "r", encoding="utf-8") as f:
            return f.read()
            
    return "Biomedical Engineering graduate (CGPA 3.77/4.00, IELTS 7.0) from Riphah International University, Pakistan, currently working as a Lab Engineer while actively pursuing PhD opportunities. Publications in Nano Energy (IF 16.8) and Chemical Engineering Journal (IF 13.4)."



def load_prompt():
    """
    Load the user-editable prompt from prompt.txt.
    Rana's fixed personal details are substituted in automatically.
    Editing prompt.txt takes effect immediately without restarting the server.
    """
    if os.path.exists(PROMPT_PATH):
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            template = f.read().strip()
    else:
        template = 'Write a personalized outreach email for a PhD position.'

    template = (
        template
        .replace("[Your Full Name]", "Rana Talha Khalid")
        .replace("[Your First Name]", "Rana")
        .replace("[your full name]", "Rana Talha Khalid")
        .replace("[Your University]", "Riphah International University")
        .replace("[your university]", "Riphah International University")
        .replace("CGPA of [X.X/4.0]", "CGPA of 3.77/4.00")
        .replace("CGPA of [X.X/4.00]", "CGPA of 3.77/4.00")
        .replace("[X.X/4.00]", "3.77/4.00")
        .replace("[X.X/4.0]", "3.77/4.00")
        .replace("[CGPA]", "3.77/4.00")
        .replace("[IELTS]", "7.0")
    )
    return template


def call_deepseek(prompt: str, api_key: str, max_retries: int = 5) -> str:
    """Call the DeepSeek API via the OpenAI-compatible SDK and return the generated text."""
    import time
    from openai import OpenAI, RateLimitError

    client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert academic email writer. Your emails are indistinguishable "
                            "from those written by a brilliant, highly motivated human student who spent "
                            "real time reading the professor's work. "
                            "NEVER use these phrases or anything like them: 'I hope this message finds you well', "
                            "'I am writing to express', 'I have been following your work', 'I came across your profile', "
                            "'resonated with me', 'left a deep impression', 'I am passionate about', "
                            "'aligns perfectly with', 'I would be honored', 'your esteemed lab', 'groundbreaking'. "
                            "NEVER insert hard line breaks inside a paragraph — every paragraph is one continuous line. "
                            "Separate paragraphs with a single blank line only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.85,
                max_tokens=3000,
            )
            choice = response.choices[0]
            finish_reason = choice.finish_reason
            if finish_reason == "length":
                print(f"Warning: DeepSeek output was truncated (finish_reason=length). "
                      f"Consider reducing prompt size. Attempt {attempt+1}.")
            text = choice.message.content
            if text:
                return text.strip()
            print(f"DeepSeek returned empty content on attempt {attempt+1}. Retrying...")
            time.sleep(3)
        except RateLimitError:
            sleep_time = 5 * (2 ** attempt)
            print(f"DeepSeek 429 rate limit hit. Retrying in {sleep_time}s (attempt {attempt+1}/{max_retries})")
            time.sleep(sleep_time)
            if attempt == max_retries - 1:
                raise
    raise ValueError("DeepSeek API returned no data after retries")


def parse_email_output(raw: str) -> dict:
    """Parse DeepSeek output into subject + body."""
    lines = raw.strip().splitlines()
    subject = ""
    body_lines = []
    body_started = False

    for i, line in enumerate(lines):
        if line.lower().startswith("subject:") and not body_started:
            subject = line[len("subject:"):].strip()
        elif subject and not body_started:
            # Skip blank line after subject
            if line.strip():
                body_started = True
                body_lines.append(line)
        elif body_started:
            body_lines.append(line)

    if not subject:
        subject = "PhD Research Inquiry"

    # Collapse hard line-wraps inside paragraphs:
    # Split on blank lines to identify paragraph boundaries, then
    # join each paragraph's internal lines into one continuous line.
    raw_body = "\n".join(body_lines).strip()
    paragraphs = raw_body.split("\n\n")
    clean_paragraphs = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Check if this paragraph is the signature block (contains the sender name)
        if "rana talha khalid" in para.lower() and any(
            w in para.lower() for w in ["regards", "sincerely", "best", "warm"]
        ):
            # Preserve intentional line breaks in the signature
            clean_paragraphs.append(para)
        else:
            # Flatten any mid-paragraph hard wraps into a single line
            clean_paragraphs.append(" ".join(line.strip() for line in para.splitlines() if line.strip()))
    body = "\n\n".join(clean_paragraphs)

    # Ensure the signature is always appended cleanly
    signature = "\n\nBest regards,\nRana Talha Khalid\nTalha.k.rajpoot@gmail.com"
    if "rana talha khalid" not in body.lower()[-120:]:
        body = body + signature

    return {"subject": subject, "body": body}


def generate_valid_email(prompt: str, api_key: str, min_words: int = 80, max_attempts: int = 3) -> dict:
    """Generate an email via DeepSeek and retry if it's too short (safety layer).
    Always returns the best result found — never raises on word count.
    """
    import time
    best = None
    best_count = 0
    for attempt in range(max_attempts):
        try:
            raw = call_deepseek(prompt, api_key)
            parsed = parse_email_output(raw)
            word_count = len(parsed["body"].split())
            if word_count > best_count:
                best = parsed
                best_count = word_count
            if word_count >= min_words:
                return parsed
            print(f"Generated email too short ({word_count} words). Retrying ({attempt+1}/{max_attempts})...")
            time.sleep(3)
        except Exception as e:
            print(f"DeepSeek attempt {attempt+1} failed: {e}")
            time.sleep(5)
    if best and best_count > 10:
        print(f"Warning: returning best email with only {best_count} words after {max_attempts} attempts.")
        return best
    raise ValueError(f"DeepSeek returned unusable output after {max_attempts} attempts. Last word count: {best_count}")


def _send_email_smtp(to_email: str, subject: str, body: str, env: dict, attach_cv: bool = True):
    """
    Send an email via Gmail SMTP with proper anti-spam headers.
    Uses multipart/alternative (text + HTML), correct From display name,
    Message-ID, Date, and Reply-To to maximize deliverability.
    """
    import smtplib
    import uuid
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders
    from email.utils import formatdate, make_msgid

    sender_addr = env.get("GMAIL_ADDRESS", "")
    password = env.get("GMAIL_APP_PASSWORD", "")
    sender_name = "Rana Talha Khalid"

    if not sender_addr or not password:
        raise ValueError("GMAIL_ADDRESS or GMAIL_APP_PASSWORD not set in .env")

    # Build a simple HTML version for better deliverability
    html_body = "<html><body style='font-family:Arial,sans-serif;font-size:14px;line-height:1.6;color:#222;max-width:680px;'>"
    for para in body.strip().split("\n\n"):
        para = para.strip()
        if para:
            # Preserve intentional line breaks for the signature
            if "Rana Talha Khalid" in para and ("Regards" in para or "Sincerely" in para or "Best" in para):
                html_body += f"<p>{para.replace(chr(10), '<br>')}</p>"
            else:
                # Remove artificial hard wraps inside normal paragraphs
                clean_para = para.replace(chr(10), ' ')
                html_body += f"<p>{clean_para}</p>"
    html_body += "</body></html>"

    # Build MIME message with proper structure
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{sender_addr}>"
    msg["To"] = to_email
    msg["Reply-To"] = f"{sender_name} <{sender_addr}>"
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="gmail.com")
    # These headers strongly signal legitimate personal email
    msg["X-Mailer"] = "Python/3"
    msg["MIME-Version"] = "1.0"

    # Attach plain text + HTML alternatives
    alt_part = MIMEMultipart("alternative")
    alt_part.attach(MIMEText(body, "plain", "utf-8"))
    alt_part.attach(MIMEText(html_body, "html", "utf-8"))
    msg.attach(alt_part)

    # Attach CV PDF if available
    if attach_cv:
        pdf_path = os.path.join(BASE_DIR, "Rana_Talha_Khalid_CV__.pdf")
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
            part = MIMEBase("application", "pdf")
            part.set_payload(pdf_data)
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                "attachment",
                filename="Rana_Talha_Khalid_CV.pdf"
            )
            msg.attach(part)

    # Use SMTP with STARTTLS (port 587) — Gmail's preferred method
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender_addr, password)
        server.sendmail(sender_addr, [to_email], msg.as_bytes())


def _send_test_email(to_email: str = "talha.k.rajpoot@gmail.com"):
    """Send a test email using a sample professor profile to verify deliverability."""
    env = load_env()
    api_key = env.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY missing in .env")

    cv_text = load_cv()

    # Sample professor profile for testing
    test_prof = {
        "name": "Prof. John Smith (TEST)",
        "title": "Associate Professor",
        "university": "University of Test",
        "department": "Biomedical Engineering",
        "email": to_email,
        "bio": "Research on wearable biosensors, flexible electronics, and AI-based health monitoring systems.",
        "interests": "wearable sensors, biosensors, AI diagnostics, medical imaging",
        "matched_keywords": "wearable sensors, AI, biosensors",
        "profile_url": "",
    }

    prompt = (
        f"{load_prompt()}\n\n"
        f"RANA TALHA KHALID'S CV / BACKGROUND:\n"
        f"{cv_text}\n\n"
        f"Key technical highlights to draw from when making specific connections (CRITICAL: Rana is NOT a student, he is a Biomedical Engineer and current Lab Engineer who graduated in 2025):\n"
        f"- Graduated in 2025 with a B.Sc. in Biomedical Engineering (CGPA 3.77/4.00, IELTS 7.0) from Riphah International University, Lahore, Pakistan.\n"
        f"- Currently works as a Lab Engineer at Riphah International University (since Oct 2025).\n"
        f"- Has an outstanding publication record of 6 published peer-reviewed Q1 papers and 2 under review.\n"
        f"- Co-First Author of a paper in Nano Energy (IF 16.8) on PVDF-based self-powered wearable cardiac monitoring and energy harvesting.\n"
        f"- Co-First Author of two papers in Chemical Engineering Journal (IF 13.4) on AI-integrated wearable sensors and next-generation wearable ECG systems.\n"
        f"- First-author manuscript under review in Sensors on ResNet-based ECG cardiac age estimation with explainable AI (Integrated Gradients).\n"
        f"- Developed 'UPEC' (Final Year Project): a multi-modal handheld portable cardiac diagnostics device capturing ECG, PCG, and PPG with a hybrid LSTM-CNN classifier (AUC > 97%). Full pipeline from analog front-end conditioning to custom embedded processing and ML.\n"
        f"- Strong experience with COMSOL Multiphysics (modeling hydrogel-based biosensors), electrospinning PVDF films, and explainable deep learning (Integrated Gradients, Grad-CAM).\n\n"
        f"PROFESSOR PROFILE:\n"
        f"Name: {test_prof['name']}\n"
        f"Title: {test_prof['title']}\n"
        f"University: {test_prof['university']}\n"
        f"Department: {test_prof['department']}\n"
        f"Matched Keywords: {test_prof['matched_keywords']}\n"
        f"Research Interests: {test_prof['interests']}\n"
        f"Bio: {test_prof['bio']}\n\n"
        f"Generate the personalized outreach email now."
    )

    parsed = generate_valid_email(prompt, api_key)
    _send_email_smtp(to_email, f"[TEST] {parsed['subject']}", parsed["body"], env, attach_cv=True)
    return {"subject": parsed["subject"], "body": parsed["body"], "sent_to": to_email}


def clean_scraped_name(name: str) -> str:
    """Clean typical scraping metadata, newlines, extra whitespaces, and prefixes."""
    import re
    if not name:
        return ""
    name = name.replace("\n", " ").replace("\r", " ").strip()
    name = re.sub(r'\s+', ' ', name)
    
    prefixes_to_strip = [
        "learn more about",
        "profile of",
        "about",
        "dr.",
        "prof.",
        "professor",
        "dr",
        "prof"
    ]
    
    while True:
        cleaned_any = False
        name_lower = name.lower()
        for prefix in prefixes_to_strip:
            if name_lower.startswith(prefix + " "):
                name = name[len(prefix) + 1:].strip()
                cleaned_any = True
                break
            elif name_lower.startswith(prefix):
                name = name[len(prefix):].strip()
                cleaned_any = True
                break
        if not cleaned_any:
            break
            
    if name.islower() or name.isupper():
        name = name.title()
        
    return name.strip()


def is_generic_email(email: str) -> bool:
    """Check if the email is a generic inbox/administrative contact."""
    if not email or "@" not in email:
        return True
    prefix = email.split("@")[0].lower().strip()
    generic_prefixes = {
        "info", "webmaster", "admissions", "contact", "support", "office", "admin", "help", 
        "marketing", "sales", "jobs", "careers", "recruitment", "press", "media", "webmaster-eng",
        "ece", "ee", "dean", "advising", "undergrad", "grad", "admit", "apply", "registrar", 
        "library", "alumni", "giving", "services", "feedback", "general", "enquiry", "enquiries", 
        "queries", "academic", "helpdesk", "postmaster", "hostmaster", "news", "mail", "inbox",
        "contact-us", "contactus"
    }
    return prefix in generic_prefixes


def verify_and_clean_professor(prof, api_key: str) -> tuple:
    """
    Verify if the profile represents a real individual professor and clean details.
    Uses local fast filtering, followed by selective low-temperature DeepSeek analysis if name is suspicious.
    Accepts either a dictionary or a Professor object, and returns (is_valid, cleaned_item, reason).
    """
    is_object = not isinstance(prof, dict)
    if is_object:
        prof_data = {
            "name": getattr(prof, "name", ""),
            "university": getattr(prof, "university", ""),
            "department": getattr(prof, "department", ""),
            "title": getattr(prof, "title", ""),
            "profile_url": getattr(prof, "profile_url", ""),
            "email": getattr(prof, "email", ""),
            "bio": getattr(prof, "bio", ""),
            "research_interests": getattr(prof, "research_interests", []),
            "publications": getattr(prof, "publications", []),
        }
    else:
        prof_data = prof

    email = prof_data.get("email", "").strip()
    name = prof_data.get("name", "").strip()
    title = prof_data.get("title", "").strip()
    
    if not email:
        return False, prof, "No email address present."
        
    if is_generic_email(email):
        return False, prof, f"Filtered as generic/department inbox: {email}"
        
    cleaned_name = clean_scraped_name(name)
    name_lower = cleaned_name.lower()
    generic_keywords = {
        "directory", "faculty", "staff", "department", "admissions", "office", "admin", 
        "university", "school", "college", "center", "institute", "webmaster", "graduate", 
        "undergraduate", "study", "research", "lab", "group", "inbox", "mail", "contact", 
        "email", "placeholder", "unknown", "website", "adjunct", "postdoc", "visitor", 
        "memoriam", "alumni", "wall of fame", "resources", "courtesy faculty", "visiting faculty", 
        "retired faculty", "emeritus faculty", "lecturer", "instructor", "about", "profile of"
    }
    
    is_suspicious = (
        len(cleaned_name) < 3
        or name_lower in generic_keywords
        or any(word in name_lower.split() for word in ["and", "for", "in", "of", "&"])
        or not any(c.isalpha() for c in cleaned_name)
    )
    
    if not is_suspicious:
        if is_object:
            prof.name = cleaned_name
            return True, prof, "Locally verified clean name."
        else:
            cleaned_data = dict(prof_data)
            cleaned_data["name"] = cleaned_name
            return True, cleaned_data, "Locally verified clean name."
            
    print(f"[*] Name '{name}' looks generic/suspicious. Invoking DeepSeek verification...")
    
    bio = prof_data.get("bio", "") or ""
    pubs = prof_data.get("publications", []) or []
    pub_titles = []
    for pub in pubs:
        if isinstance(pub, dict) and pub.get("title"):
            pub_titles.append(pub["title"])
        elif hasattr(pub, "title") and pub.title:
            pub_titles.append(pub.title)
    pub_titles_str = " | ".join(pub_titles[:5])
    
    interests = prof_data.get("research_interests", [])
    if isinstance(interests, list):
        interests_str = ", ".join(interests[:15])
    else:
        interests_str = str(interests)
        
    prompt = (
        "Analyze this scraped academic profile and extract the real person's name and academic title. "
        "Sometimes the scraped name is a generic term (like 'Faculty', 'Staff', 'AI and Society', 'Systems and Networking') or includes junk prefixes. "
        "If it is a generic office contact, general inquiry box, administrative staff who is NOT a research professor/faculty, or just a research area/topic, mark it invalid.\n\n"
        f"Scraped Name: {name}\n"
        f"Scraped Title: {title}\n"
        f"Scraped Email: {email}\n"
        f"University: {prof_data.get('university', '')}\n"
        f"Department: {prof_data.get('department', '')}\n"
        f"Bio/Description: {bio[:800]}\n"
        f"Research Interests: {interests_str}\n"
        f"Publication Titles: {pub_titles_str}\n\n"
        "Respond strictly in JSON format with these exact keys:\n"
        "{\n"
        "  \"is_valid\": true or false,\n"
        "  \"extracted_name\": \"Cleaned real name of the professor (e.g. 'Chaouki Abdallah') or empty if invalid\",\n"
        "  \"extracted_title\": \"Cleaned academic title (e.g. 'Assistant Professor') or empty if invalid\",\n"
        "  \"reason\": \"Brief explanation of your decision (e.g., 'Placeholder name corrected using bio' or 'Generic department inbox skipped')\"\n"
        "}"
    )
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
        
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "You are a precise data extraction agent. You output raw JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content.strip()
        import json
        data = json.loads(result_text)
        
        valid = data.get("is_valid", False)
        if valid:
            ext_name = clean_scraped_name(data.get("extracted_name", ""))
            ext_title = data.get("extracted_title", "").strip()
            
            if ext_name and not any(w in ext_name.lower() for w in generic_keywords):
                if is_object:
                    prof.name = ext_name
                    if ext_title:
                        prof.title = ext_title
                    return True, prof, f"LLM verified: {data.get('reason')}"
                else:
                    cleaned_data = dict(prof_data)
                    cleaned_data["name"] = ext_name
                    if ext_title:
                        cleaned_data["title"] = ext_title
                    return True, cleaned_data, f"LLM verified: {data.get('reason')}"
            else:
                return False, prof, f"LLM returned invalid/generic name: {ext_name}"
        else:
            return False, prof, f"LLM flagged invalid: {data.get('reason')}"
            
    except Exception as e:
        print(f"Error in LLM verification: {e}")
        if len(cleaned_name) >= 3 and name_lower not in generic_keywords:
            if is_object:
                prof.name = cleaned_name
                return True, prof, f"LLM error: {e}, fallback to local polished name."
            else:
                cleaned_data = dict(prof_data)
                cleaned_data["name"] = cleaned_name
                return True, cleaned_data, f"LLM error: {e}, fallback to local polished name."
        return False, prof, f"LLM error: {e}, rejected generic placeholder."


def _run_mass_email_campaign():
    """Background thread to process all professors and send emails."""
    status_path = os.path.join(RESULTS_DIR, "mass_email_status.json")
    
    def save_status(data):
        with open(status_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
    # ── Persistent sent-email log (survives restarts) ─────────────────────
    SENT_LOG_FILE = os.path.join(RESULTS_DIR, "sent_log.json")

    def load_sent_log():
        if os.path.exists(SENT_LOG_FILE):
            try:
                with open(SENT_LOG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return set(e.lower() for e in data.get("sent_emails", []))
            except Exception:
                pass
        return set()

    def add_to_sent_log(email_addr, sent_set, log_entries):
        sent_set.add(email_addr.lower())
        os.makedirs(RESULTS_DIR, exist_ok=True)
        with open(SENT_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump({"sent_emails": list(sent_set), "log": log_entries}, f, indent=4)

    status = {
        "status": "running",
        "total": 0,
        "sent": 0,
        "failed": 0,
        "skipped": 0,
        "current_prof": "Starting...",
        "log": []
    }
    save_status(status)

    try:
        import time
        env = load_env()
        api_key = env.get("DEEPSEEK_API_KEY", "")

        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY missing in .env")
        if not env.get("GMAIL_ADDRESS") or not env.get("GMAIL_APP_PASSWORD"):
            raise ValueError("GMAIL_ADDRESS or GMAIL_APP_PASSWORD missing in .env. Required for SMTP.")

        cache_path = os.path.join(BASE_DIR, "cache.json")
        if not os.path.exists(cache_path):
            raise ValueError("No professors found (cache.json is missing). Run a scan first.")

        with open(cache_path, "r", encoding="utf-8") as f:
            professors = json.load(f)

        from matcher import KeywordMatcher
        from models import Professor, Publication
        matcher = KeywordMatcher()

        prof_objects = []
        for entry in professors:
            p = Professor(
                name=entry.get("name", ""),
                university=entry.get("university", ""),
                department=entry.get("department", ""),
                title=entry.get("title", ""),
                profile_url=entry.get("profile_url", ""),
                email=entry.get("email", ""),
                research_interests=entry.get("research_interests", []),
                bio=entry.get("bio", ""),
                scholar_url=entry.get("scholar_url", ""),
            )
            for pub_data in entry.get("publications", []):
                p.publications.append(Publication(**pub_data))
            prof_objects.append(p)

        scored = matcher.filter_professors(prof_objects, min_score=0.5)
        profs_with_email = [p for p in scored if p.email]

        # Load persistent sent log — skip already-emailed professors
        already_sent = load_sent_log()
        remaining = [p for p in profs_with_email if p.email.lower() not in already_sent]
        skipped = len(profs_with_email) - len(remaining)

        # Restore previous log entries so history stays visible
        existing_log = []
        skipped_count = 0
        if os.path.exists(SENT_LOG_FILE):
            try:
                with open(SENT_LOG_FILE, "r", encoding="utf-8") as f:
                    existing_log = json.load(f).get("log", [])
                skipped_count = sum(1 for entry in existing_log if "Skipped" in entry.get("result", ""))
            except Exception:
                pass

        status["total"] = len(profs_with_email)
        status["sent"] = max(0, len(already_sent) - skipped_count)
        status["skipped"] = skipped_count
        status["log"] = existing_log
        status["current_prof"] = f"Resuming — {status['sent']} sent, {skipped_count} skipped, {len(remaining)} remaining."
        save_status(status)

        print(f"Campaign: {len(profs_with_email)} total, {status['sent']} sent, {skipped_count} skipped, {len(remaining)} remaining.")
        cv_text = load_cv()

        for prof in remaining:
            # Check disk-based stop flag (survives server restarts)
            if _is_stop_requested():
                status["status"] = "stopped"
                status["current_prof"] = "Stopped by user."
                save_status(status)
                return

            # ── STEP 0: Verify and Clean Professor Details ─────────────────
            is_valid, cleaned_prof, skip_reason = verify_and_clean_professor(prof, api_key)
            if not is_valid:
                print(f"[*] Skipping {prof.name} ({prof.email}): {skip_reason}")
                status["log"].insert(0, {
                    "name": prof.name, "email": prof.email,
                    "match": getattr(prof, 'match_level', ''), "university": prof.university,
                    "subject": "N/A", "word_count": 0,
                    "result": f"Skipped: {skip_reason}", "time": time.strftime("%H:%M:%S")
                })
                # Add to persistent sent log so we don't process them again next time
                add_to_sent_log(prof.email, already_sent, status["log"])
                status["skipped"] += 1
                status["current_prof"] = f"Skipped: {prof.name}"
                save_status(status)
                continue

            prof_name = prof.name
            prof_email = prof.email
            status["current_prof"] = f"{prof_name} ({prof_email}) — {prof.match_level}"
            save_status(status)

            try:
                interests = ", ".join(prof.research_interests[:20])
                matched_kw = ", ".join(prof.matched_keywords[:10])
                bio = (prof.bio or "")[:1000]

                # ── STEP 1: Building prompt ───────────────────────────────
                status["pipeline_step"] = 1
                status["pipeline_label"] = "Building prompt..."
                status["pipeline_prompt"] = ""
                status["pipeline_output"] = ""
                status["pipeline_subject"] = ""
                status["pipeline_body"] = ""
                status["pipeline_word_count"] = 0
                save_status(status)

                prompt = (
                    f"{load_prompt()}\n\n"
                    f"RANA TALHA KHALID'S CV / BACKGROUND:\n"
                    f"{cv_text}\n\n"
                    f"Key technical highlights to draw from when making specific connections (CRITICAL: Rana is NOT a student, he is a Biomedical Engineer and current Lab Engineer who graduated in 2025):\n"
                    f"- Graduated in 2025 with a B.Sc. in Biomedical Engineering (CGPA 3.77/4.00, IELTS 7.0) from Riphah International University, Lahore, Pakistan.\n"
                    f"- Currently works as a Lab Engineer at Riphah International University (since Oct 2025).\n"
                    f"- Has an outstanding publication record of 6 published peer-reviewed Q1 papers and 2 under review.\n"
                    f"- Co-First Author of a paper in Nano Energy (IF 16.8) on PVDF-based self-powered wearable cardiac monitoring and energy harvesting.\n"
                    f"- Co-First Author of two papers in Chemical Engineering Journal (IF 13.4) on AI-integrated wearable sensors and next-generation wearable ECG systems.\n"
                    f"- First-author manuscript under review in Sensors on ResNet-based ECG cardiac age estimation with explainable AI (Integrated Gradients).\n"
                    f"- Developed 'UPEC' (Final Year Project): a multi-modal handheld portable cardiac diagnostics device capturing ECG, PCG, and PPG with a hybrid LSTM-CNN classifier (AUC > 97%). Full pipeline from analog front-end conditioning to custom embedded processing and ML.\n"
                    f"- Strong experience with COMSOL Multiphysics (modeling hydrogel-based biosensors), electrospinning PVDF films, and explainable deep learning (Integrated Gradients, Grad-CAM).\n\n"
                    f"PROFESSOR PROFILE:\n"
                    f"Name: {prof_name}\n"
                    f"Title: {prof.title or 'Faculty'}\n"
                    f"University: {prof.university}\n"
                    f"Department: {prof.department}\n"
                    f"Matched Keywords: {matched_kw}\n"
                    f"Research Interests: {interests}\n"
                    f"Bio/Research Description:\n{bio}\n\n"
                    f"Generate the personalized outreach email now."
                )
                # Store a readable excerpt of the prompt (first 1200 chars)
                status["pipeline_prompt"] = prompt[:1200] + ("..." if len(prompt) > 1200 else "")
                status["pipeline_step"] = 2
                status["pipeline_label"] = "Prompt ready — calling DeepSeek AI..."
                save_status(status)

                # ── STEP 2: Call DeepSeek ─────────────────────────────────
                raw = call_deepseek(prompt, api_key)
                status["pipeline_output"] = raw[:2000] + ("..." if len(raw) > 2000 else "")
                status["pipeline_step"] = 3
                status["pipeline_label"] = "AI response received — parsing email..."
                save_status(status)

                # ── STEP 3: Parse & validate ──────────────────────────────
                parsed = parse_email_output(raw)
                word_count = len(parsed["body"].split())
                # Retry if too short (mirrors generate_valid_email logic inline)
                attempts = 1
                while word_count < 80 and attempts < 3:
                    print(f"Email too short ({word_count}w), retrying attempt {attempts+1}...")
                    raw = call_deepseek(prompt, api_key)
                    parsed = parse_email_output(raw)
                    word_count = len(parsed["body"].split())
                    attempts += 1

                status["pipeline_subject"] = parsed["subject"]
                status["pipeline_body"] = parsed["body"]
                status["pipeline_word_count"] = word_count
                status["pipeline_step"] = 4
                status["pipeline_label"] = f"Email ready ({word_count} words) — sending via SMTP..."
                save_status(status)

                # ── STEP 4: Send email ────────────────────────────────────
                _send_email_smtp(prof_email, parsed["subject"], parsed["body"], env)

                # ── STEP 5: Mark sent ─────────────────────────────────────
                add_to_sent_log(prof_email, already_sent, status["log"])
                status["sent"] += 1
                status["pipeline_step"] = 5
                status["pipeline_label"] = f"Sent! Waiting 15s before next professor..."
                status["log"].insert(0, {
                    "name": prof_name, "email": prof_email,
                    "match": prof.match_level, "university": prof.university,
                    "subject": parsed["subject"],
                    "word_count": word_count,
                    "result": "Sent", "time": time.strftime("%H:%M:%S")
                })
                save_status(status)

                # 15 second delay — respects DeepSeek rate limits & Gmail daily quota
                time.sleep(15)


            except Exception as e:
                status["failed"] += 1
                status["log"].insert(0, {
                    "name": prof_name, "email": prof_email,
                    "match": getattr(prof, 'match_level', ''),
                    "result": f"Error: {str(e)}", "time": time.strftime("%H:%M:%S")
                })

            save_status(status)
            
        status["status"] = "completed"
        status["current_prof"] = "Done"
        save_status(status)
        
    except Exception as e:
        status["status"] = "error"
        status["current_prof"] = f"Fatal Error: {str(e)}"
        save_status(status)


def _generate_campaign_page():
    """Generate a standalone campaign progress tracking page."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    campaign_page = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Campaign Pipeline — AdvisorScout</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#050508;--surface:#0d0d18;--card:#111120;--border:rgba(255,255,255,0.07);
  --text:#ffffff;--text2:#9090b0;--accent:#7d5fff;--accent2:#b3a4ff;
  --green:#00d2ad;--orange:#ff9f43;--red:#ff6b6b;--blue:#48dbfb;
}
body{font-family:'Outfit',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;
  background-image:radial-gradient(ellipse at top,rgba(125,95,255,0.08) 0%,transparent 60%),
                   radial-gradient(ellipse at bottom right,rgba(0,210,173,0.05) 0%,transparent 50%);}
.topnav{display:flex;align-items:center;justify-content:space-between;
  padding:1.2rem 2.5rem;border-bottom:1px solid var(--border);
  background:rgba(5,5,8,0.9);backdrop-filter:blur(20px);position:sticky;top:0;z-index:100;}
.nav-brand{display:flex;align-items:center;gap:12px;}
.nav-brand h1{font-size:1.3rem;font-weight:800;
  background:linear-gradient(135deg,var(--accent2),var(--blue));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.nav-links{display:flex;gap:1rem;}
.nav-link{color:var(--text2);text-decoration:none;font-size:.85rem;font-weight:600;
  padding:.5rem 1.2rem;border-radius:10px;transition:all .2s;border:1px solid transparent;}
.nav-link:hover,.nav-link.active{color:var(--text);background:rgba(255,255,255,0.06);border-color:var(--border);}
.nav-link.active{color:var(--accent2);border-color:rgba(125,95,255,0.3);}
.page{max-width:1400px;margin:0 auto;padding:2rem;}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-bottom:1.5rem;}
@media(max-width:900px){.two-col{grid-template-columns:1fr;}}
.status-hero{background:linear-gradient(135deg,rgba(125,95,255,0.08),rgba(0,210,173,0.06));
  border:1px solid rgba(125,95,255,0.2);border-radius:24px;padding:2rem;margin-bottom:1.5rem;position:relative;overflow:hidden;}
.status-hero::before{content:'';position:absolute;top:0;right:0;width:300px;height:300px;
  background:radial-gradient(circle,rgba(125,95,255,0.15),transparent 70%);pointer-events:none;}
.hero-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1.5rem;flex-wrap:wrap;gap:1rem;}
.hero-left h2{font-size:1.8rem;font-weight:800;margin-bottom:.3rem;}
.hero-left p{color:var(--text2);font-size:.88rem;}
.campaign-badge{display:inline-flex;align-items:center;gap:8px;
  padding:.6rem 1.4rem;border-radius:50px;font-weight:700;font-size:.85rem;}
.badge-running{background:rgba(0,210,173,0.12);color:var(--green);border:1px solid rgba(0,210,173,0.3);}
.badge-stopped{background:rgba(255,107,107,0.12);color:var(--red);border:1px solid rgba(255,107,107,0.3);}
.badge-completed{background:rgba(0,210,173,0.12);color:var(--green);border:1px solid rgba(0,210,173,0.3);}
.badge-idle{background:rgba(144,144,176,0.12);color:var(--text2);border:1px solid var(--border);}
.badge-error{background:rgba(255,107,107,0.12);color:var(--red);border:1px solid rgba(255,107,107,0.3);}
.badge-interrupted{background:rgba(255,159,67,0.12);color:var(--orange);border:1px solid rgba(255,159,67,0.3);}
.pulse{width:9px;height:9px;border-radius:50%;background:var(--green);animation:pulse 1.5s ease-in-out infinite;display:inline-block;}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1);}50%{opacity:.5;transform:scale(1.4);}}
.prog-section{margin-bottom:.5rem;}
.prog-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:.6rem;}
.prog-header span{font-size:.85rem;font-weight:600;color:var(--text2);}
.prog-header strong{font-size:1rem;color:var(--accent2);}
.prog-track{height:12px;background:rgba(255,255,255,0.05);border-radius:10px;overflow:hidden;}
.prog-fill{height:100%;border-radius:10px;
  background:linear-gradient(90deg,var(--accent),var(--blue),var(--green));
  background-size:200% 100%;animation:shimmer 2s linear infinite;
  transition:width .6s ease;min-width:2px;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:0% 0}}
.metrics-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:1rem;margin-bottom:1.5rem;}
@media(max-width:900px){.metrics-grid{grid-template-columns:repeat(3,1fr);}}
.metric-card{background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:16px;
  padding:1.2rem;text-align:center;transition:border-color .2s;}
.metric-card:hover{border-color:rgba(125,95,255,0.3);}
.metric-num{font-size:2rem;font-weight:800;letter-spacing:-1px;display:block;margin-bottom:.25rem;}
.metric-num.green{color:var(--green);}.metric-num.orange{color:var(--orange);}
.metric-num.red{color:var(--red);}.metric-num.blue{color:var(--blue);}.metric-num.accent{color:var(--accent2);}
.metric-label{font-size:.68rem;color:var(--text2);text-transform:uppercase;letter-spacing:1.5px;font-weight:600;}
.controls-bar{display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:1.5rem;}
.ctrl-btn{display:inline-flex;align-items:center;gap:.6rem;
  padding:.75rem 1.5rem;border-radius:12px;font-family:'Outfit',sans-serif;
  font-weight:700;font-size:.85rem;cursor:pointer;transition:all .25s;border:none;}
.btn-start{background:linear-gradient(135deg,var(--green),#00b894);color:#fff;box-shadow:0 6px 20px rgba(0,210,173,0.3);}
.btn-start:hover{transform:translateY(-2px);box-shadow:0 10px 28px rgba(0,210,173,0.45);}
.btn-stop{background:linear-gradient(135deg,var(--red),#c0392b);color:#fff;box-shadow:0 6px 20px rgba(255,107,107,0.3);}
.btn-stop:hover{transform:translateY(-2px);box-shadow:0 10px 28px rgba(255,107,107,0.4);}
.btn-reset{background:rgba(255,255,255,0.06);color:var(--text2);border:1px solid var(--border);}
.btn-reset:hover{background:rgba(255,255,255,0.1);color:var(--text);}
.btn-test{background:rgba(72,219,251,0.1);color:var(--blue);border:1px solid rgba(72,219,251,0.25);}
.btn-test:hover{background:rgba(72,219,251,0.18);}
.alert{padding:1rem 1.4rem;border-radius:14px;font-size:.88rem;margin-bottom:1.2rem;display:none;}
.alert.show{display:flex;align-items:center;gap:1rem;}
.alert-success{background:rgba(0,210,173,0.08);border:1px solid rgba(0,210,173,0.3);color:var(--green);}
.alert-error{background:rgba(255,107,107,0.08);border:1px solid rgba(255,107,107,0.3);color:var(--red);}
/* PIPELINE */
.pipeline-card{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:1.5rem;margin-bottom:1.5rem;}
.pipeline-card h3{font-size:.75rem;font-weight:700;margin-bottom:1.2rem;color:var(--text2);text-transform:uppercase;letter-spacing:1px;}
.pipeline{display:flex;gap:0;align-items:flex-start;}
.pipe-step{flex:1;display:flex;flex-direction:column;align-items:center;position:relative;}
.pipe-step:not(:last-child)::after{content:'';position:absolute;top:20px;left:calc(50% + 22px);
  right:calc(-50% + 22px);height:2px;background:var(--border);z-index:0;}
.pipe-step.done::after{background:var(--green);}
.pipe-step.active::after{background:linear-gradient(90deg,var(--accent),var(--border));}
.pipe-icon{width:44px;height:44px;border-radius:50%;display:flex;align-items:center;
  justify-content:center;font-size:1.1rem;border:2px solid var(--border);
  background:var(--surface);z-index:1;position:relative;transition:all .4s;}
.pipe-step.done .pipe-icon{background:rgba(0,210,173,0.15);border-color:var(--green);}
.pipe-step.active .pipe-icon{background:rgba(125,95,255,0.2);border-color:var(--accent2);
  box-shadow:0 0 18px rgba(125,95,255,0.5);animation:glow 1.5s ease-in-out infinite;}
@keyframes glow{0%,100%{box-shadow:0 0 10px rgba(125,95,255,0.3);}50%{box-shadow:0 0 24px rgba(125,95,255,0.7);}}
.pipe-label{font-size:.65rem;color:var(--text2);margin-top:.5rem;text-align:center;
  font-weight:600;text-transform:uppercase;letter-spacing:.5px;max-width:80px;line-height:1.3;}
.pipe-step.done .pipe-label{color:var(--green);}
.pipe-step.active .pipe-label{color:var(--accent2);}
/* CURRENT PROFESSOR */
.current-card{background:rgba(125,95,255,0.06);border:1px solid rgba(125,95,255,0.2);
  border-radius:16px;padding:1.2rem 1.5rem;margin-bottom:1.5rem;display:flex;align-items:center;gap:1rem;}
.current-icon{font-size:1.5rem;}
.current-text{flex:1;}
.current-text .label{font-size:.68rem;color:var(--accent2);text-transform:uppercase;letter-spacing:1.5px;font-weight:700;}
.current-text .value{font-size:.95rem;font-weight:600;color:var(--text);margin-top:2px;}
.step-label{font-size:.8rem;color:var(--green);margin-top:.3rem;font-style:italic;}
/* PANELS */
.panel{background:var(--card);border:1px solid var(--border);border-radius:20px;overflow:hidden;}
.panel-header{padding:1rem 1.4rem;border-bottom:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;cursor:pointer;
  user-select:none;transition:background .2s;}
.panel-header:hover{background:rgba(255,255,255,0.02);}
.panel-header h3{font-size:.85rem;font-weight:700;display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;}
.panel-tag{font-size:.63rem;padding:.2rem .6rem;border-radius:6px;font-weight:700;}
.tag-prompt{background:rgba(72,219,251,0.12);color:var(--blue);}
.tag-output{background:rgba(125,95,255,0.12);color:var(--accent2);}
.tag-email{background:rgba(0,210,173,0.12);color:var(--green);}
.tag-wc{background:rgba(255,159,67,0.12);color:var(--orange);}
.panel-toggle{font-size:.75rem;color:var(--text2);transition:transform .3s;flex-shrink:0;}
.panel-toggle.open{transform:rotate(180deg);}
.panel-body{padding:1.2rem 1.4rem;display:none;max-height:380px;overflow-y:auto;}
.panel-body.open{display:block;}
.panel-pre{font-family:'Courier New',monospace;font-size:.76rem;line-height:1.7;color:var(--text2);
  white-space:pre-wrap;word-break:break-word;}
.email-subject{font-size:.95rem;font-weight:700;color:var(--accent2);
  margin-bottom:.8rem;padding:.6rem 1rem;background:rgba(125,95,255,0.08);
  border-radius:10px;border-left:3px solid var(--accent);}
.email-body-text{font-size:.85rem;line-height:1.9;color:var(--text);white-space:pre-wrap;}
/* LOG */
.section-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;}
.section-header h3{font-size:1rem;font-weight:700;color:var(--text);}
.section-header .sub{font-size:.8rem;color:var(--text2);}
.log-wrap{overflow-x:auto;border-radius:16px;border:1px solid var(--border);margin-bottom:2rem;}
.log-table{width:100%;border-collapse:collapse;}
.log-table th{background:rgba(255,255,255,0.03);padding:.8rem 1rem;
  text-align:left;font-size:.63rem;color:var(--text2);
  text-transform:uppercase;letter-spacing:1.5px;font-weight:700;
  border-bottom:1px solid var(--border);white-space:nowrap;}
.log-table td{padding:.75rem 1rem;border-bottom:1px solid rgba(255,255,255,0.04);
  font-size:.8rem;vertical-align:middle;}
.log-table tr:last-child td{border-bottom:none;}
.log-table tr:hover td{background:rgba(255,255,255,0.02);}
.status-sent{display:inline-flex;align-items:center;gap:4px;color:var(--green);font-weight:700;font-size:.75rem;}
.status-error{display:inline-flex;align-items:center;gap:4px;color:var(--red);font-weight:600;font-size:.72rem;
  max-width:200px;word-break:break-word;white-space:normal;}
.match-high{color:var(--orange);font-weight:700;font-size:.73rem;}
.match-good{color:var(--blue);font-weight:600;font-size:.73rem;}
.match-partial{color:var(--text2);font-size:.73rem;}
.email-cell{color:var(--text2);font-size:.75rem;font-family:monospace;}
.time-cell{color:var(--text2);font-size:.73rem;white-space:nowrap;}
.name-cell{font-weight:600;font-size:.83rem;}
.univ-cell{font-size:.73rem;color:var(--text2);}
.wc-cell{font-size:.73rem;color:var(--orange);font-weight:600;}
.subj-cell{font-size:.73rem;color:var(--accent2);max-width:180px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.empty-log{text-align:center;padding:3rem;color:var(--text2);font-size:.9rem;}
.refresh-dot{width:8px;height:8px;border-radius:50%;background:var(--green);
  display:inline-block;margin-right:6px;animation:pulse 1.5s infinite;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-track{background:transparent;}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:6px;}
::-webkit-scrollbar-thumb:hover{background:rgba(255,255,255,0.12);}
</style>
</head>
<body>

<nav class="topnav">
  <div class="nav-brand">
    <span style="font-size:1.5rem">📊</span>
    <h1>Campaign Pipeline</h1>
  </div>
  <div class="nav-links">
    <a href="/" class="nav-link">&#127968; Dashboard</a>
    <a href="/campaign" class="nav-link active">&#128202; Campaign</a>
  </div>
</nav>

<div class="page">

  <div class="alert alert-success" id="alert-success"><span>OK</span><span id="alert-text"></span></div>
  <div class="alert alert-error" id="alert-error"><span>!!</span><span id="alert-err-text"></span></div>

  <!-- HERO -->
  <div class="status-hero">
    <div class="hero-top">
      <div class="hero-left">
        <h2 id="hero-title">Email Campaign</h2>
        <p id="hero-sub">Checking status...</p>
      </div>
      <div id="campaign-badge" class="campaign-badge badge-idle">Loading...</div>
    </div>
    <div class="prog-section">
      <div class="prog-header">
        <span id="prog-label">Progress</span>
        <strong id="prog-pct">0%</strong>
      </div>
      <div class="prog-track"><div class="prog-fill" id="prog-fill" style="width:0%"></div></div>
    </div>
  </div>

  <!-- METRICS -->
  <div class="metrics-grid">
    <div class="metric-card"><span class="metric-num accent" id="m-total">--</span><span class="metric-label">Total</span></div>
    <div class="metric-card"><span class="metric-num green" id="m-sent">--</span><span class="metric-label">Sent</span></div>
    <div class="metric-card"><span class="metric-num red" id="m-failed">--</span><span class="metric-label">Failed</span></div>
    <div class="metric-card"><span class="metric-num blue" id="m-skipped">--</span><span class="metric-label">Skipped</span></div>
    <div class="metric-card"><span class="metric-num orange" id="m-remaining">--</span><span class="metric-label">Remaining</span></div>
    <div class="metric-card"><span class="metric-num blue" id="m-rate">--</span><span class="metric-label">Success Rate</span></div>
  </div>

  <!-- CONTROLS -->
  <div class="controls-bar">
    <button class="ctrl-btn btn-start" id="btn-start" onclick="startCampaign()">&#9654; Start Campaign</button>
    <button class="ctrl-btn btn-stop" id="btn-stop" onclick="stopCampaign()" style="display:none">&#9632; Stop</button>
    <button class="ctrl-btn btn-reset" onclick="resetCampaign()">Reset Status</button>
    <button class="ctrl-btn btn-test" onclick="sendTestEmail()">Test Email</button>
    <button class="ctrl-btn btn-reset" onclick="window.location.href='/'">Back to Dashboard</button>
  </div>

  <!-- PIPELINE -->
  <div class="pipeline-card">
    <h3>Live Pipeline Steps</h3>
    <div class="pipeline">
      <div class="pipe-step idle" id="pipe-1">
        <div class="pipe-icon">&#128203;</div>
        <div class="pipe-label">Build Prompt</div>
      </div>
      <div class="pipe-step idle" id="pipe-2">
        <div class="pipe-icon">&#129302;</div>
        <div class="pipe-label">Call DeepSeek AI</div>
      </div>
      <div class="pipe-step idle" id="pipe-3">
        <div class="pipe-icon">&#9986;</div>
        <div class="pipe-label">Parse Email</div>
      </div>
      <div class="pipe-step idle" id="pipe-4">
        <div class="pipe-icon">&#128232;</div>
        <div class="pipe-label">Send via SMTP</div>
      </div>
      <div class="pipe-step idle" id="pipe-5">
        <div class="pipe-icon">&#8987;</div>
        <div class="pipe-label">Cooldown 15s</div>
      </div>
    </div>
  </div>

  <!-- CURRENT PROFESSOR -->
  <div class="current-card">
    <div class="current-icon">&#127919;</div>
    <div class="current-text">
      <div class="label">Currently Processing</div>
      <div class="value" id="current-prof-text">--</div>
      <div class="step-label" id="step-label">--</div>
    </div>
  </div>

  <!-- PROMPT + OUTPUT (2 col) -->
  <div class="two-col">
    <div class="panel">
      <div class="panel-header" onclick="togglePanel('prompt-body','prompt-toggle')">
        <h3>Prompt Sent to DeepSeek <span class="panel-tag tag-prompt">PROMPT</span></h3>
        <span class="panel-toggle" id="prompt-toggle">&#9660;</span>
      </div>
      <div class="panel-body" id="prompt-body">
        <div class="panel-pre" id="prompt-text">No prompt yet. Start the campaign to see live data.</div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header" onclick="togglePanel('output-body','output-toggle')">
        <h3>DeepSeek Raw Output <span class="panel-tag tag-output">AI OUTPUT</span></h3>
        <span class="panel-toggle" id="output-toggle">&#9660;</span>
      </div>
      <div class="panel-body" id="output-body">
        <div class="panel-pre" id="output-text">Waiting for AI response...</div>
      </div>
    </div>
  </div>

  <!-- EMAIL PREVIEW (full width) -->
  <div class="panel" style="margin-bottom:1.5rem;">
    <div class="panel-header" onclick="togglePanel('email-panel-body','email-toggle')">
      <h3>Parsed Email Preview
        <span class="panel-tag tag-email">EMAIL</span>
        <span class="panel-tag tag-wc" id="wc-tag">-- words</span>
      </h3>
      <span class="panel-toggle" id="email-toggle">&#9660;</span>
    </div>
    <div class="panel-body" id="email-panel-body">
      <div class="email-subject" id="email-subject">Subject: --</div>
      <div class="email-body-text" id="email-body-text">No email generated yet.</div>
    </div>
  </div>

  <!-- LOG TABLE -->
  <div class="section-header">
    <h3><span class="refresh-dot"></span>Activity Log</h3>
    <span class="sub" id="log-count">Loading...</span>
  </div>
  <div class="log-wrap">
    <table class="log-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Professor</th>
          <th>University</th>
          <th>Email</th>
          <th>Subject</th>
          <th>Words</th>
          <th>Match</th>
          <th>Status</th>
          <th>Time</th>
        </tr>
      </thead>
      <tbody id="log-tbody">
        <tr><td colspan="9" class="empty-log">Waiting for campaign data...</td></tr>
      </tbody>
    </table>
  </div>

</div>

<script>
function escHtml(s){
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function togglePanel(bodyId, toggleId){
  const body=document.getElementById(bodyId);
  const tog=document.getElementById(toggleId);
  const isOpen=body.classList.contains('open');
  body.classList.toggle('open',!isOpen);
  tog.classList.toggle('open',!isOpen);
}

let panelsAutoOpened=false;

async function poll(){
  try{
    const res=await fetch('/mass_email_status.json?t='+Date.now());
    if(!res.ok) return;
    const s=await res.json();
    updateStatus(s);
  }catch(e){console.warn('Poll failed:',e);}
}

function updateStatus(s){
  const total=s.total||0, sent=s.sent||0, failed=s.failed||0, skipped=s.skipped||0;
  const remaining=Math.max(0,total-sent-failed-skipped);
  const pct=total>0?Math.min(100,Math.round(((sent+failed+skipped)/total)*100)):0;
  const rate=(sent+failed)>0?Math.round((sent/(sent+failed))*100):0;

  document.getElementById('m-total').textContent=total||'--';
  document.getElementById('m-sent').textContent=sent;
  document.getElementById('m-failed').textContent=failed;
  document.getElementById('m-skipped').textContent=skipped;
  document.getElementById('m-remaining').textContent=remaining>0?remaining:(total>0?'0':'--');
  document.getElementById('m-rate').textContent=(sent+failed)>0?rate+'%':'--';
  document.getElementById('prog-fill').style.width=pct+'%';
  document.getElementById('prog-pct').textContent=pct+'%';
  document.getElementById('prog-label').textContent=(sent+skipped)+' of '+total+' processed';
  document.getElementById('current-prof-text').textContent=s.current_prof||'--';
  document.getElementById('step-label').textContent=s.pipeline_label||'';

  // Pipeline steps
  const step=s.pipeline_step||0;
  for(let i=1;i<=5;i++){
    const el=document.getElementById('pipe-'+i);
    if(!el) continue;
    el.className='pipe-step '+(i<step?'done':i===step?'active':'idle');
  }

  // Prompt
  if(s.pipeline_prompt){
    document.getElementById('prompt-text').textContent=s.pipeline_prompt;
    if(!panelsAutoOpened){
      togglePanel('prompt-body','prompt-toggle');
      togglePanel('output-body','output-toggle');
      togglePanel('email-panel-body','email-toggle');
      panelsAutoOpened=true;
    }
  }
  // AI output
  if(s.pipeline_output) document.getElementById('output-text').textContent=s.pipeline_output;
  // Email preview
  if(s.pipeline_subject) document.getElementById('email-subject').textContent='Subject: '+s.pipeline_subject;
  if(s.pipeline_body) document.getElementById('email-body-text').textContent=s.pipeline_body;
  const wc=s.pipeline_word_count||0;
  document.getElementById('wc-tag').textContent=wc>0?wc+' words':'-- words';

  // Badge + hero
  const badge=document.getElementById('campaign-badge');
  const btnStart=document.getElementById('btn-start');
  const btnStop=document.getElementById('btn-stop');
  badge.className='campaign-badge';
  if(s.status==='running'){
    badge.classList.add('badge-running');
    badge.innerHTML='<span class="pulse"></span> Running';
    document.getElementById('hero-title').textContent='Email Campaign Active';
    document.getElementById('hero-sub').textContent='Sending via DeepSeek AI  |  '+sent+'/'+total+' complete';
    btnStart.style.display='none'; btnStop.style.display='flex';
  }else if(s.status==='completed'){
    badge.classList.add('badge-completed'); badge.textContent='Completed';
    document.getElementById('hero-title').textContent='Campaign Complete!';
    document.getElementById('hero-sub').textContent='All '+total+' professors processed  |  '+sent+' sent  |  '+failed+' failed';
    btnStart.style.display='flex'; btnStop.style.display='none';
  }else if(s.status==='stopped'){
    badge.classList.add('badge-stopped'); badge.textContent='Stopped';
    document.getElementById('hero-title').textContent='Campaign Stopped';
    document.getElementById('hero-sub').textContent='Manually stopped  |  '+sent+' sent so far';
    btnStart.style.display='flex'; btnStop.style.display='none';
  }else if(s.status==='error'){
    badge.classList.add('badge-error'); badge.textContent='Error';
    document.getElementById('hero-title').textContent='Campaign Error';
    document.getElementById('hero-sub').textContent=s.current_prof||'An error occurred';
    btnStart.style.display='flex'; btnStop.style.display='none';
  }else if(s.status==='interrupted'){
    badge.classList.add('badge-interrupted'); badge.textContent='Interrupted';
    document.getElementById('hero-title').textContent='Campaign Interrupted';
    document.getElementById('hero-sub').textContent='Server restarted. Click Start to resume.';
    btnStart.style.display='flex'; btnStop.style.display='none';
  }else{
    badge.classList.add('badge-idle'); badge.textContent='Idle';
    document.getElementById('hero-title').textContent='Email Campaign';
    document.getElementById('hero-sub').textContent='No active campaign. Click Start to begin.';
    btnStart.style.display='flex'; btnStop.style.display='none';
  }

  // Log table
  const log=s.log||[];
  const tbody=document.getElementById('log-tbody');
  document.getElementById('log-count').textContent=log.length+' entries';
  if(log.length===0){
    tbody.innerHTML='<tr><td colspan="9" class="empty-log">No activity yet. Start the campaign.</td></tr>';
    return;
  }
  tbody.innerHTML=log.map((entry,i)=>{
    const isSent=entry.result==='Sent';
    const statusCell=isSent
      ?'<span class="status-sent">Sent</span>'
      :'<span class="status-error">'+escHtml(entry.result)+'</span>';
    const matchCell=(entry.match||'').includes('High')
      ?'<span class="match-high">'+escHtml(entry.match)+'</span>'
      :(entry.match||'').includes('Good')
        ?'<span class="match-good">'+escHtml(entry.match)+'</span>'
        :'<span class="match-partial">'+escHtml(entry.match||'--')+'</span>';
    return '<tr>'+
      '<td style="color:var(--text2);font-size:.72rem;">'+(log.length-i)+'</td>'+
      '<td class="name-cell">'+escHtml(entry.name||'--')+'</td>'+
      '<td class="univ-cell">'+escHtml(entry.university||'--')+'</td>'+
      '<td class="email-cell">'+escHtml(entry.email||'--')+'</td>'+
      '<td class="subj-cell" title="'+escHtml(entry.subject||'')+'">'+escHtml(entry.subject||'--')+'</td>'+
      '<td class="wc-cell">'+(entry.word_count?entry.word_count+'w':'--')+'</td>'+
      '<td>'+matchCell+'</td>'+
      '<td>'+statusCell+'</td>'+
      '<td class="time-cell">'+escHtml(entry.time||'--')+'</td>'+
      '</tr>';
  }).join('');
}

async function startCampaign(){
  if(!confirm('Start the email campaign? Emails will be sent to all matched professors via DeepSeek AI.')) return;
  panelsAutoOpened=false;
  try{ await fetch('/start_mass_email'); showAlert('success','Campaign started! Watching for updates...'); }
  catch(e){ showAlert('error','Failed to start: '+e.message); }
}
async function stopCampaign(){
  if(!confirm('Stop the campaign? Progress is saved.')) return;
  try{ await fetch('/stop_mass_email'); showAlert('success','Stop signal sent. Will halt after current email.'); }
  catch(e){ showAlert('error','Failed to stop: '+e.message); }
}
async function resetCampaign(){
  if(!confirm('Reset campaign status? This does NOT clear the sent log.')) return;
  try{ await fetch('/reset_campaign'); showAlert('success','Status reset.'); panelsAutoOpened=false; }
  catch(e){ showAlert('error','Failed to reset: '+e.message); }
}
async function sendTestEmail(){
  document.querySelectorAll('.ctrl-btn').forEach(b=>b.disabled=true);
  showAlert('success','Sending test email...');
  try{
    const res=await fetch('/send_test_email');
    const data=await res.json();
    if(data.status==='sent') showAlert('success','Test sent to '+data.sent_to+'! Subject: "'+data.subject+'"');
    else showAlert('error','Test failed: '+(data.message||'Unknown error'));
  }catch(e){ showAlert('error','Test email failed: '+e.message); }
  finally{ document.querySelectorAll('.ctrl-btn').forEach(b=>b.disabled=false); }
}
function showAlert(type,msg){
  document.getElementById('alert-success').classList.remove('show');
  document.getElementById('alert-error').classList.remove('show');
  if(type==='success'){
    document.getElementById('alert-text').textContent=msg;
    document.getElementById('alert-success').classList.add('show');
    setTimeout(()=>document.getElementById('alert-success').classList.remove('show'),6000);
  }else{
    document.getElementById('alert-err-text').textContent=msg;
    document.getElementById('alert-error').classList.add('show');
    setTimeout(()=>document.getElementById('alert-error').classList.remove('show'),8000);
  }
}
setInterval(poll,2000);
poll();
</script>
</body>
</html>"""
    campaign_path = os.path.join(RESULTS_DIR, "campaign_progress.html")
    with open(campaign_path, "w", encoding="utf-8") as f:
        f.write(campaign_page)



class ScraperHandler(http.server.SimpleHTTPRequestHandler):


    def do_GET(self):
        url = urlparse(self.path)

        if url.path == "/start":
            self._send_json({"status": "started"})
            thread = threading.Thread(target=self.run_scraper)
            thread.daemon = True
            thread.start()
            return

        if url.path == "/status.json":
            status_path = os.path.join(RESULTS_DIR, "status.json")
            if os.path.exists(status_path):
                self._send_file(status_path, "application/json")
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Status file not found yet.")
            return

        if url.path == "/start_mass_email":
            _clear_stop_flag()  # Remove any existing stop flag
            self._send_json({"status": "started"})
            thread = threading.Thread(target=_run_mass_email_campaign)
            thread.daemon = True
            thread.start()
            return

        if url.path == "/reset_campaign":
            """Reset campaign status so it can be restarted cleanly."""
            _clear_stop_flag()
            status_path = os.path.join(RESULTS_DIR, "mass_email_status.json")
            if os.path.exists(status_path):
                os.remove(status_path)
            self._send_json({"status": "reset"})
            return

        if url.path == "/stop_mass_email":
            _set_stop_flag()  # Write stop flag to disk
            # Also immediately update status file so UI reflects this
            status_path = os.path.join(RESULTS_DIR, "mass_email_status.json")
            if os.path.exists(status_path):
                try:
                    with open(status_path, "r", encoding="utf-8") as f:
                        s = json.load(f)
                    s["status"] = "stopped"
                    s["current_prof"] = "Stopped by user."
                    with open(status_path, "w", encoding="utf-8") as f:
                        json.dump(s, f, indent=4)
                except Exception:
                    pass
            self._send_json({"status": "stop_requested"})
            return
            
        if url.path == "/mass_email_status.json":
            status_path = os.path.join(RESULTS_DIR, "mass_email_status.json")
            if os.path.exists(status_path):
                self._send_file(status_path, "application/json")
            else:
                # Return empty status if it doesn't exist
                self._send_json({"status": "idle", "total": 0, "sent": 0, "failed": 0, "current_prof": "", "log": []})
            return

        if url.path == "/send_test_email":
            try:
                result = _send_test_email("talha.k.rajpoot@gmail.com")
                self._send_json({"status": "sent", "sent_to": result["sent_to"], "subject": result["subject"]})
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, status=500)
            return

        if url.path == "/get_keywords":
            from config import SEARCH_KEYWORDS
            self._send_json(SEARCH_KEYWORDS)
            return

        if url.path == "/get_cv":
            cv_text = load_cv()
            self._send_json({"cv": cv_text})
            return

        if url.path == "/sent_log.json":
            sent_log_path = os.path.join(RESULTS_DIR, "sent_log.json")
            if os.path.exists(sent_log_path):
                self._send_file(sent_log_path, "application/json")
            else:
                self._send_json({"sent_emails": [], "log": []})
            return

        if url.path == "/campaign":
            # Always generate the campaign page to reflect updates
            _generate_campaign_page()
            campaign_path = os.path.join(RESULTS_DIR, "campaign_progress.html")
            if os.path.exists(campaign_path):
                self._send_file(campaign_path, "text/html; charset=utf-8")
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Campaign progress page not available.")
            return

        # Serve the dashboard at root
        if self.path == "/" or self.path == "":
            if os.path.exists(DASHBOARD_PATH):
                self.path = "/results/professors_report.html"
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Dashboard not generated yet. Click 'Start' to begin.")
                return

        return super().do_GET()

    def do_POST(self):
        url = urlparse(self.path)

        if url.path == "/save_keywords":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            try:
                keywords = json.loads(post_data.decode("utf-8"))
                from config import KEYWORDS_FILE
                with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
                    json.dump(keywords, f, indent=4)
                self._send_json({"status": "success"})
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, status=500)
            return

        if url.path == "/generate_email":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            try:
                prof_data = json.loads(post_data.decode("utf-8"))
                env = load_env()
                api_key = env.get("DEEPSEEK_API_KEY", "")
                if not api_key:
                    self._send_json({"status": "error", "message": "DEEPSEEK_API_KEY not set in .env file"}, status=500)
                    return

                # ── Verification and Cleaning Layer ──
                is_valid, cleaned_prof, skip_reason = verify_and_clean_professor(prof_data, api_key)
                if not is_valid:
                    self._send_json({"status": "error", "message": f"Verification failed: {skip_reason}"}, status=400)
                    return
                prof_data = cleaned_prof

                cv_text = load_cv()
                prompt = self._build_email_prompt(prof_data, cv_text)
                parsed = generate_valid_email(prompt, api_key)
                self._send_json({"status": "success", **parsed})
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, status=500)
            return

        if url.path == "/send_email_now":
            """Send a composed email directly via SMTP."""
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8"))
                to_email = data.get("to_email", "")
                subject = data.get("subject", "")
                body = data.get("body", "")
                if not to_email or not subject or not body:
                    self._send_json({"status": "error", "message": "Missing to_email, subject, or body"}, status=400)
                    return
                env = load_env()
                _send_email_smtp(to_email, subject, body, env, attach_cv=True)
                self._send_json({"status": "sent", "to": to_email})
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, status=500)
            return

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: str, content_type: str):
        with open(path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def _build_email_prompt(self, prof: dict, cv: str) -> str:
        """Build the full DeepSeek prompt for email generation."""
        name = prof.get("name", "Professor")
        university = prof.get("university", "")
        department = prof.get("department", "")
        title = prof.get("title", "")
        email = prof.get("email", "")
        bio = prof.get("bio", "")
        interests = prof.get("interests", "")
        matched_keywords = prof.get("matched_keywords", "")
        profile_url = prof.get("profile_url", "")

        return (
            f"{load_prompt()}\n\n"
            f"RANA TALHA KHALID'S CV / BACKGROUND:\n"
            f"{cv}\n\n"
            f"Key technical highlights to draw from when making specific connections (CRITICAL: Rana is NOT a student, he is a Biomedical Engineer and current Lab Engineer who graduated in 2025):\n"
            f"- Graduated in 2025 with a B.Sc. in Biomedical Engineering (CGPA 3.77/4.00, IELTS 7.0) from Riphah International University, Lahore, Pakistan.\n"
            f"- Currently works as a Lab Engineer at Riphah International University (since Oct 2025).\n"
            f"- Has an outstanding publication record of 6 published peer-reviewed Q1 papers and 2 under review.\n"
            f"- Co-First Author of a paper in Nano Energy (IF 16.8) on PVDF-based self-powered wearable cardiac monitoring and energy harvesting.\n"
            f"- Co-First Author of two papers in Chemical Engineering Journal (IF 13.4) on AI-integrated wearable sensors and next-generation wearable ECG systems.\n"
            f"- First-author manuscript under review in Sensors on ResNet-based ECG cardiac age estimation with explainable AI (Integrated Gradients).\n"
            f"- Developed 'UPEC' (Final Year Project): a multi-modal handheld portable cardiac diagnostics device capturing ECG, PCG, and PPG with a hybrid LSTM-CNN classifier (AUC > 97%). Full pipeline from analog front-end conditioning to custom embedded processing and ML.\n"
            f"- Strong experience with COMSOL Multiphysics (modeling hydrogel-based biosensors), electrospinning PVDF films, and explainable deep learning (Integrated Gradients, Grad-CAM).\n\n"
            f"PROFESSOR PROFILE TO WRITE EMAIL FOR:\n"
            f"Name: {name}\n"
            f"Title: {title}\n"
            f"University: {university}\n"
            f"Department: {department}\n"
            f"Email: {email}\n"
            f"Profile URL: {profile_url}\n\n"
            f"Research Interests / Bio:\n"
            f"{bio if bio else interests}\n\n"
            f"Research Topics / Tags:\n"
            f"{interests}\n\n"
            f"Matched Keywords (overlap with Rana's profile):\n"
            f"{matched_keywords}\n\n"
            f"Generate the personalized outreach email now."
        )

    def run_scraper(self):
        print("Starting scraper background process...")
        try:
            subprocess.run([sys.executable, "main.py"], check=True)
            print("Scraper finished successfully.")
        except Exception as e:
            print(f"Scraper error: {e}")

    def log_message(self, format, *args):
        # Suppress routine GET logs, keep errors
        if args and str(args[1]) != "200":
            super().log_message(format, *args)




def _cleanup_on_startup():
    """Reset stale campaign state every time the server boots."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    _clear_stop_flag()
    status_path = os.path.join(RESULTS_DIR, "mass_email_status.json")
    if os.path.exists(status_path):
        try:
            with open(status_path, "r", encoding="utf-8") as f:
                s = json.load(f)
            if s.get("status") == "running":
                s["status"] = "interrupted"
                s["current_prof"] = "Server restarted. Campaign did not finish."
                with open(status_path, "w", encoding="utf-8") as f:
                    json.dump(s, f, indent=4)
                print("[!] Previous campaign interrupted. Status reset.")
        except Exception:
            pass

def run_server():
    _cleanup_on_startup()
    os.chdir(BASE_DIR)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), ScraperHandler) as httpd:
        print(f"[*] AdvisorScout server started at http://localhost:{PORT}")
        print("    Open this URL in your browser to access the dashboard.")
        httpd.serve_forever()


if __name__ == "__main__":
    run_server()
