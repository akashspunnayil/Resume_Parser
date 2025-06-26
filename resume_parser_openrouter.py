# import openai
from openai import OpenAI
import pdfplumber
import json
import sys
import os
import re
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# === Extract text from PDF ===
def extract_text(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join(p.extract_text() or '' for p in pdf.pages)

# Set OpenRouter API endpoint and key

# Set API key and base
# openai.api_key = os.getenv("OPENROUTER_API_KEY")
# openai.api_base = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")

# === Desired Skills List ===
desired_skills = [
    "Python", "Machine Learning", "Streamlit", "Data Analysis", "Deep Learning",
    "Shell scripting", "FORTRAN", "HPC", "Oceanography", "Climate Science"
]

# === Query OpenRouter LLM ===
def parse_resume(text):
    prompt = f"""
You are a professional resume parser.

From the resume text below, extract the following fields in JSON format with these exact keys:
["name", "email", "phone", "address", "skills", "education", "experience", "certifications", "links", "total_experience_years"]

- "skills", "education", "experience", and "certifications" should be returned as a list of strings.
- "total_experience_years" should be a float, estimated from the dates in experience section.

Resume:
\"\"\"
{text[:3000]}
\"\"\"

Only return valid JSON.
"""

    client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
    )

    
    response = client.chat.completions.create(
        model="mistralai/mistral-nemo",
        messages=[{"role": "user", "content": prompt}],
    )
    reply = response.choices[0].message.content.strip()


    reply = response.choices[0].message.content.strip()

    # Extract the JSON block using regex
    match = re.search(r"\{.*\}", reply, re.DOTALL)
    if match:
        json_text = match.group(0)
        try:
            return json.loads(json_text)
        except Exception as e:
            print("❌ JSON parsing failed. Extracted block but still invalid:")
            print(json_text)
            print(f"\nError: {e}")
            return None
    else:
        print("❌ No JSON object found in LLM response.")
        print(reply)
        return None

# === Match Desired Skills ===
def find_matched_skills(extracted_skills, desired_list):
    matched = []
    for skill in desired_list:
        for item in extracted_skills:
            if skill.lower() in item.lower():
                matched.append(skill)
                break
    return matched

# === Pretty Print Results ===
def print_pretty(parsed_data):
    print("\n✅ Parsed Resume Info:\n")
    for key, value in parsed_data.items():
        if key == "total_experience_years":
            continue  # We'll print this separately
        if isinstance(value, list):
            print(f"{key.capitalize()}:\n  - " + "\n  - ".join(map(str, value)) + "\n")
        elif isinstance(value, dict):
            print(f"{key.capitalize()}:")
            for k, v in value.items():
                print(f"  - {k}: {v}")
            print()
        else:
            print(f"{key.capitalize()}: {value}\n")

    # === Desired Skills Match ===
    skills = parsed_data.get("skills", [])
    matched = find_matched_skills(skills, desired_skills)
    if matched:
        print("🎯 Desired Skills Matched:\n  - " + "\n  - ".join(matched) + "\n")
    else:
        print("🎯 No desired skills matched.\n")

    # === Experience Years from LLM ===
    if "total_experience_years" in parsed_data:
        print(f"📅 Total Experience (LLM Estimated): {parsed_data['total_experience_years']} years\n")

    # === Certifications ===
    certifications = parsed_data.get("certifications", [])
    if certifications:
        print("🎓 Certifications Found:\n  - " + "\n  - ".join(certifications) + "\n")
    else:
        print("🎓 No certifications found.\n")

# === CLI Runner ===
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python resume_parser_openrouter.py resume.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not os.path.isfile(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        sys.exit(1)

    print(f"\n📄 Reading: {pdf_path}")
    resume_text = extract_text(pdf_path)

    print("\n🤖 Extracting structured info using OpenRouter LLM...")
    result = parse_resume(resume_text)

    if result:
        print_pretty(result)
    else:
        print("❌ Resume parsing failed.")
