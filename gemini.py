import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# Load .env for local development
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")

# Fall back to Streamlit secrets when deployed on Streamlit Cloud
if not api_key:
    try:
        import streamlit as st
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found. Set it in your .env file locally, "
        "or in Streamlit Cloud's Secrets settings when deployed."
    )

client = genai.Client(api_key=api_key)