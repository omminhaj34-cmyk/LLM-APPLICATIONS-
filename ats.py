import json
import time

from google.genai.errors import ServerError
from gemini import client


def analyze_resume(text, max_retries=5):
    prompt = f"""
You are an ATS resume analyzer.

Analyze the resume below and return an ATS score and feedback.

Resume:
{text}

Return JSON only with the following fields:

{{
    "ats_score": 0,
    "summary": "",
    "strengths": [],
    "weaknesses": []
}}

Rules:
- Output ONLY valid JSON.
- No markdown.
- No explanation.
- strengths and weaknesses must contain short tags only.
"""

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )

            if not response.text:
                raise ValueError("Empty response received from Gemini.")

            return json.loads(response.text)

        except ServerError:
            if attempt == max_retries - 1:
                raise

            wait = 2 ** attempt
            print(f"Server busy. Retrying in {wait} seconds...")
            time.sleep(wait)

        except json.JSONDecodeError:
            raise ValueError(
                "Gemini returned an invalid JSON response."
            )

        except Exception:
            raise