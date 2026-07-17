import time
from google.genai.errors import ServerError
from gemini import client

# Try the primary model first; if it's overloaded, fall back to a lighter model
MODEL_CANDIDATES = ["gemini-3.5-flash", "gemini-flash-lite-latest"]


def analyze_resume(text, max_retries=3):
    prompt = f"""
You are an ATS resume analyzer.

Analyze the resume below and return an ATS score and feedback.

Resume:
{text}

Return in JSON format with:
- ats_score (0-100)
- summary (2-3 sentences)
- strengths (a list of 4-6 SHORT tags, each 1-3 words only, e.g. "Python",
  "Machine Learning", "Project Management", "Cloud Architecture" — 
  NOT full sentences)
- weaknesses (a list of 4-6 SHORT tags, each 1-3 words only, e.g.
  "Missing Certifications", "Quantifiable Metrics", "Keyword Density",
  "Volunteer Gap" — NOT full sentences)

Rules:
- Output ONLY JSON
- No extra text
- strengths and weaknesses must be short tags/keywords, never full sentences
"""

    last_error = None
    for model_name in MODEL_CANDIDATES:
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
                    time.sleep(3 * (attempt + 1))  # 3s, 6s, 9s backoff
                    continue
                # exhausted retries on this model, try the next model in the list
                break

    # all models and retries exhausted
    raise last_error