import os
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)

HEADERS = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": GEMINI_API_KEY,
}


def translate(text: str, target_language: str) -> str:
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            f"Translate the following Hindi text into natural, fluent "
                            f"{target_language}. Preserve meaning.\n\n{text}"
                        )
                    }
                ],
            }
        ]
    }

    res = requests.post(
        GEMINI_URL,
        headers=HEADERS,
        json=payload,
        timeout=20,
    )
    res.raise_for_status()

    return res.json()["candidates"][0]["content"]["parts"][0]["text"]


def translate_to_english_and_czech(text: str) -> dict:
    return {
        "english": translate(text, "English"),
        "czech": translate(text, "Czech"),
    }
