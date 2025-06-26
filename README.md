# 📄 Resume Parser (Streamlit + LLM)

[View App](https://a-resume-parser.streamlit.app/)

A Streamlit web app that uses an LLM (via OpenRouter API) to extract structured information from multiple PDF resumes. The app displays a table where each row represents a resume, and columns include personal details, reported and matched skills, certifications, and estimated years of experience.

---

## 🚀 Features

- ✅ Upload multiple PDF resumes
- 🤖 Extracts:
  - Name, Email, Phone, Address
  - Skills (reported and matched)
  - Education, Experience, Certifications
  - Estimated Total Experience (years)
  - External links (GitHub, LinkedIn, etc.)
- 📊 Displays results in a table format
- 📥 Download the parsed results as a CSV file

---

## 🔐 API Setup

Set your [OpenRouter API key](https://openrouter.ai/) and base URL securely using environment variables:

```bash
export OPENROUTER_API_KEY="sk-xxxxxxxxxxxxxxxxxx"
export OPENROUTER_API_BASE="https://openrouter.ai/api/v1"

