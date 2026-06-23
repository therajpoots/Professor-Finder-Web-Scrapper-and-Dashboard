content = open('app.py', 'r', encoding='utf-8').read().replace('\r\n', '\n')

load_prompt_fn = '''

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
        template = EMAIL_SYSTEM_PROMPT

    template = (
        template
        .replace("[Your Full Name]", "Rana Talha Khalid")
        .replace("[Your First Name]", "Rana")
        .replace("[your full name]", "Rana Talha Khalid")
        .replace("[Your University]", "NED University of Engineering & Technology")
        .replace("[your university]", "NED University of Engineering & Technology")
        .replace("CGPA of [X.X/4.0]", "CGPA of 3.8/4.0")
        .replace("[X.X/4.0]", "3.8/4.0")
        .replace(
            "[list your research interests here, e.g., developing biomaterials for tissue regeneration, "
            "AI-driven analysis of medical imaging, and smart drug delivery systems]",
            "wearable biosensors and self-powered health monitoring systems, "
            "AI-driven biomedical diagnostics and explainable clinical decision support, "
            "and BioMEMS microfluidic device design for point-of-care applications"
        )
    )
    return template

'''

# Inject load_prompt after load_cv function
marker = '\ndef call_gemini('
if marker in content:
    content = content.replace(marker, load_prompt_fn + '\ndef call_gemini(', 1)
    print('Injected load_prompt OK')
else:
    print('Marker not found')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done. Lines:', content.count('\n'))
