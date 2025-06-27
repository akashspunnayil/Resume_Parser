import streamlit as st
#import openai
import pdfplumber
import pandas as pd
import json
import re
#from io import BytesIO
#import os

#from dotenv import load_dotenv
#load_dotenv()


# === CONFIGURE API ===

from openai import OpenAI


# # Create OpenAI client using Streamlit secrets
# client = OpenAI(
#     api_key=st.secrets["OPENROUTER_API_KEY"],
#     base_url=st.secrets["OPENROUTER_API_BASE"]
# )
st.sidebar.subheader("🔐 API Key Configuration")
st.sidebar.markdown(
    """
    <div style='font-size: 0.85em; line-height: 1.4'>
        This app uses a Large Language Model (LLM) to extract structured information from resumes.<br><br>
        To use the LLM service (e.g., OpenRouter), an API key is required for secure access.<br><br>
        You can get a free API key by signing up at 
        <a href="https://openrouter.ai" target="_blank">openrouter.ai</a> and generating a key from your account dashboard.<br><br>        
    </div>
    """,
    unsafe_allow_html=True
)

api_mode = st.sidebar.radio("Choose API Key Mode", ["Use Streamlit Secrets", "Manually Enter API Key"])

if api_mode == "Manually Enter API Key":
    api_key_input = st.sidebar.text_input("Enter OpenRouter API Key", type="password")
    api_base_input = st.sidebar.text_input("Enter API Base URL", value="https://openrouter.ai/api/v1")

    if not api_key_input:
        st.warning("⚠️ Please enter your API key.")
        st.stop()

    # Use manually entered key
    client = OpenAI(
        api_key=api_key_input,
        base_url=api_base_input
    )
else:
    # Use Streamlit secrets
    client = OpenAI(
        api_key=st.secrets["OPENROUTER_API_KEY"],
        base_url=st.secrets["OPENROUTER_API_BASE"]
    )


# Extract text from PDF
def extract_text(file):
    with pdfplumber.open(file) as pdf:
        return "\n".join(p.extract_text() or '' for p in pdf.pages)

# Call LLM and extract JSON
def parse_resume(text):
#     prompt = f"""
# You are a professional resume parser.

# From the resume text below, extract the following fields in JSON format with these exact keys:
# ["name", "email", "phone", "address", "skills", "education", "experience", "certifications", "links", "total_experience_years"]

# Return a valid JSON only.

# Resume:
# \"\"\"
# {text[:3000]}
# \"\"\"
# """

    prompt = f"""
You are a professional resume parser.

From the resume text below, extract the following fields in JSON format using these exact keys:
["name", "email", "phone", "address", "skills", "education", "experience", "certifications", "links", "total_experience_years"]

Extraction Guidelines:
- **skills**: Extract all actual tools, software, programming languages, etc., listed under any skill-related headings or subheadings (e.g., "Software Skills", "Technical Skills"). Do **not** include section headers as skills.
- **education**: Extract **exactly as written** in the resume, preserving full degree names, institution names, marks/scores/cgpa/opgpa/grades and year ranges. Do not abbreviate or summarize. If bullet points or multiple entries exist, return them all as a list.
- **certifications**: Include any NET/JRF, and any other qualifications/certifications mentioned in text.
- **experience**: Include each role's title, organization, and full duration exactly as written. If any role includes a time period (e.g., "03/2023 – Present" or "May 2022 - Oct 2022"), make sure it is listed and considered.
- **total_experience_years**: 
    - Calculate the total experience in years by summing durations from all valid date ranges found in the experience section.
    - Include internships, research projects, dissertations, part-time work, or full-time roles **if they mention a time range**.
    - Treat any of these terms as ongoing: "Present", "Ongoing", "Currently working", "Pursuing", "Till date", etc.
    - Always treat ongoing roles as continuing up to **June 2025**.
    - Round the total experience to 2 decimal places (e.g., 2.75).

Return only a valid JSON object with no additional explanation.

Resume:
\"\"\"
{text[:4000]}
\"\"\"
"""

    
# - **total_experience_years**: Estimate the total professional experience by summing up job durations, even if the total is not explicitly stated. Return as float (because if months included included in experiences listed).

    try:
        response = client.chat.completions.create(
            model="mistralai/mistral-nemo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        reply = response.choices[0].message.content.strip()
        return json.loads(re.search(r"\{.*\}", reply, re.DOTALL).group(0))
    except Exception as e:
        return {"error": str(e)}


# === Desired Skills ===
desired_skills = [
    "Python", "Machine Learning", "Streamlit", "Data Analysis", "Deep Learning",
    "Shell scripting", "FORTRAN", "HPC", "Oceanography", "Climate Science"
]

# === Match desired skills ===
# def match_skills(skills):
#     return [skill for skill in desired_skills if any(skill.lower() in s.lower() for s in skills)]

def match_skills(skills):
    matched = [skill for skill in desired_skills if any(skill.lower() in s.lower() for s in skills)]
    unmatched = [s for s in skills if not any(ds.lower() in s.lower() for ds in desired_skills)]
    return matched, unmatched

# === Streamlit App ===
st.set_page_config(page_title="Resume Parser", layout="wide")
st.title("📄 Resume Parser - Details Extraction")

uploaded_files = st.file_uploader("Upload one or more resumes (PDF)", type="pdf", accept_multiple_files=True)

if uploaded_files:
    data = []
    for file in uploaded_files:
        with st.spinner(f"Parsing {file.name}..."):
            text = extract_text(file)
            parsed = parse_resume(text)

            if "error" in parsed:
                st.error(f"{file.name}: {parsed['error']}")
                continue

            # reported_skills = parsed.get("skills", [])
            # matched_skills = match_skills(reported_skills)

            reported_skills = parsed.get("skills", [])
            matched_skills, unmatched_skills = match_skills(reported_skills)

            
            data.append({
                "File": file.name,
                "Name": parsed.get("name"),
                "Email": parsed.get("email"),
                "Phone": parsed.get("phone"),
                "Address": parsed.get("address"),
                "Education":parsed.get("education"),
                "Other Reported Skills": ", ".join(unmatched_skills),
                "Matched Skills": ", ".join(matched_skills),
                "Experience":parsed.get("experience"),
                "Experience (Years)": parsed.get("total_experience_years"),
                "Certifications": "; ".join(parsed.get("certifications", [])),
                "Links": "; ".join(parsed.get("links", []))
            })


    df = pd.DataFrame(data)
    st.success("✅ Parsing completed!")

    st.subheader("📊 Parsed Results")
    st.dataframe(df, use_container_width=True)

    # CSV Download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", csv, "parsed_resumes.csv", "text/csv")

