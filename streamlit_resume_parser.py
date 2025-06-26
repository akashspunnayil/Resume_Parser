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

import streamlit as st
from openai import OpenAI
import pdfplumber
import pandas as pd
import json
import re

# Create OpenAI client using Streamlit secrets
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
    prompt = f"""
You are a professional resume parser.

From the resume text below, extract the following fields in JSON format with these exact keys:
["name", "email", "phone", "address", "skills", "education", "experience", "certifications", "links", "total_experience_years"]

Return a valid JSON only.

Resume:
\"\"\"
{text[:3000]}
\"\"\"
"""
    try:
        response = client.chat.completions.create(
            model="mistralai/mistral-nemo",
            messages=[{"role": "user", "content": prompt}]
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
def match_skills(skills):
    return [skill for skill in desired_skills if any(skill.lower() in s.lower() for s in skills)]

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

            # matched_skills = match_skills(parsed.get("skills", []))
            # data.append({
            #     "File": file.name,
            #     "Name": parsed.get("name"),
            #     "Email": parsed.get("email"),
            #     "Phone": parsed.get("phone"),
            #     "Address": parsed.get("address"),
            #     "Matched Skills": ", ".join(matched_skills),
            #     "Experience (Years)": parsed.get("total_experience_years"),
            #     "Certifications": "; ".join(parsed.get("certifications", [])),
            #     "Links": "; ".join(parsed.get("links", []))
            # })

            reported_skills = parsed.get("skills", [])
            matched_skills = match_skills(reported_skills)
            
            data.append({
                "File": file.name,
                "Name": parsed.get("name"),
                "Email": parsed.get("email"),
                "Phone": parsed.get("phone"),
                "Address": parsed.get("address"),
                "Reported Skills": ", ".join(reported_skills),
                "Matched Skills": ", ".join(matched_skills),
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

