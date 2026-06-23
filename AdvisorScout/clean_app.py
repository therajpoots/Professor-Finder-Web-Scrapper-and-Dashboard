import os

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if line.startswith('EMAIL_SYSTEM_PROMPT = """'):
        skip = True
        continue
    if skip and 'Nothing else. No explanations. No meta text. No markdown. Just the subject line then the email body."""' in line:
        skip = False
        continue
    if skip:
        continue
    
    # Update load_prompt fallback
    if "template = EMAIL_SYSTEM_PROMPT" in line:
        line = line.replace("template = EMAIL_SYSTEM_PROMPT", "template = 'Write a personalized outreach email for a PhD position.'")
        
    # Also clean up the comment above EMAIL_SYSTEM_PROMPT
    if line.startswith("# ── System prompt for email generation"):
        continue

    new_lines.append(line)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Cleaned up redundant code!")
