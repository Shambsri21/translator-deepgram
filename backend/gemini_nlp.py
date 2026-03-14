import os
import re
import time
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent"
)


def _get_headers() -> dict:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY missing")
    return {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": gemini_api_key,
    }


def _post_with_retry(payload: dict, retries: int = 3) -> dict:
    """POST to Gemini with exponential backoff on 429."""
    delay = 2
    for attempt in range(retries):
        res = requests.post(
            GEMINI_URL, headers=_get_headers(), json=payload, timeout=30
        )
        if res.status_code == 429 and attempt < retries - 1:
            time.sleep(delay)
            delay *= 2
            continue
        res.raise_for_status()
        return res.json()
    res.raise_for_status()


def translate_to_english_and_czech(text: str) -> dict:
    """Single API call that returns both English and Czech translations."""
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Translate the following Hindi text into both English and Czech. "
                            "Respond with ONLY a JSON object in this exact format, no extra text:\n"
                            '{"english": "<English translation>", "czech": "<Czech translation>"}\n\n'
                            f"Hindi text: {text}"
                        )
                    }
                ],
            }
        ],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    data = _post_with_retry(payload)
    raw = data["candidates"][0]["content"]["parts"][0]["text"]

    try:
        import json

        result = json.loads(raw)
        return {
            "english": result.get("english", ""),
            "czech": result.get("czech", ""),
        }
    except Exception:
        # Fallback: extract with regex if JSON parse fails
        english = re.search(r'"english"\s*:\s*"([^"]+)"', raw)
        czech = re.search(r'"czech"\s*:\s*"([^"]+)"', raw)
        return {
            "english": english.group(1) if english else raw,
            "czech": czech.group(1) if czech else "",
        }
