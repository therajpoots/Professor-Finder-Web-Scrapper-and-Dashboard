import os
import sys
from dotenv import load_dotenv

# Add the workspace directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import load_prompt, load_cv, call_deepseek, generate_valid_email

def main():
    # Load .env
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        print("[ERROR] DEEPSEEK_API_KEY not found in env.")
        # Try loading directly from .env file
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("DEEPSEEK_API_KEY="):
                        api_key = line.split("=")[1].strip()
        if not api_key:
            print("[ERROR] Still no API key found. Exiting.")
            sys.exit(1)

    print(f"[OK] API Key loaded: {api_key[:10]}...")

    cv_text = load_cv()
    print("[OK] CV loaded successfully.")

    # 1. Prof. Yuce (Wearable Sensors & Energy Harvesting focus)
    prof_yuce = {
        "name": "Mehmet Yuce",
        "title": "Professor",
        "university": "Monash University",
        "department": "Electrical and Computer Systems Engineering",
        "email": "mehmet.yuce@monash.edu",
        "bio": "Mehmet Yuce is a professor working on self-powered implantable biosensors, cuff-less blood pressure monitoring, wearable cardiac diagnostics, energy harvesting, and low-power telemetry.",
        "interests": "self-powered implantable biosensors, cuff-less blood pressure monitoring, wearable sensors, energy harvesting, biomedical devices",
        "matched_keywords": "wearable sensors, biosensors, energy harvesting",
        "profile_url": "https://research.monash.edu/en/persons/mehmet-yuce"
    }

    # 2. Prof. Jane Boyd (AI/ML Diagnostics focus)
    prof_boyd = {
        "name": "Stephen Boyd",
        "title": "Professor",
        "university": "Stanford University",
        "department": "Electrical Engineering",
        "email": "boyd@stanford.edu",
        "bio": "Research focus on machine learning algorithms, deep learning for time-series physiological data, AI-based diagnostics in clinical medicine, and explainable neural network frameworks.",
        "interests": "machine learning, deep learning, AI diagnostics, neural networks, explainable AI",
        "matched_keywords": "machine learning, deep learning, explainable AI",
        "profile_url": "https://profiles.stanford.edu/stephen-boyd"
    }

    test_cases = [
        ("Mehmet Yuce", prof_yuce),
        ("Stephen Boyd", prof_boyd)
    ]

    for label, prof in test_cases:
        print("\n" + "="*80)
        print(f"Generating cold email for {label}...")
        print("="*80)

        # Re-construct the exact prompt used by AdvisorScout
        interests = prof.get("interests", "")
        matched_kw = prof.get("matched_keywords", "")
        bio = prof.get("bio", "")

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
            f"Name: {prof['name']}\n"
            f"Title: {prof['title']}\n"
            f"University: {prof['university']}\n"
            f"Department: {prof['department']}\n"
            f"Matched Keywords: {matched_kw}\n"
            f"Research Interests: {interests}\n"
            f"Bio/Research Description:\n{bio}\n\n"
            f"Generate the personalized outreach email now."
        )

        try:
            parsed = generate_valid_email(prompt, api_key)
            print("\nGenerated Subject:")
            print(parsed["subject"])
            print("\nGenerated Body:")
            print(parsed["body"])
            print("\nWord Count:", len(parsed["body"].split()))
        except Exception as e:
            print(f"[ERROR] Failed to generate email: {e}")

if __name__ == "__main__":
    main()
