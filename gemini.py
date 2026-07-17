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


def generate_with_retry(prompt, max_retries=3):
    """Calls Gemini with automatic retry + model fallback on overload (503) errors."""
    import time
    from google.genai.errors import ServerError

    model_candidates = ["gemini-3.5-flash", "gemini-flash-lite-latest"]
    last_error = None

    for model_name in model_candidates:
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                return response.text
            except ServerError as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(3 * (attempt + 1))
                    continue
                break

    raise last_error