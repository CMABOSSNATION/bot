"""
Google Gemini AI integration (FREE)
Replaces Claude API - works the same way
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

SYSTEM_PROMPT = """You are a friendly WhatsApp assistant for DevUG, a software development company in Kampala, Uganda.

The company offers:
- Website development (from UGX 500,000)
- Mobile app development Android & iOS (from UGX 2,000,000)
- Custom software & management systems (from UGX 3,000,000)
- WhatsApp bots for businesses (from UGX 500,000)
- UI/UX Design (from UGX 300,000)

Contact: +256 700 000000 | hello@devug.com | www.devug.com
Location: Kampala, Uganda
Hours: Mon-Fri 8am-6pm, Sat 9am-2pm

Rules:
- Keep replies SHORT and conversational (max 150 words)
- Be warm and friendly
- If asked about prices give the starting prices above
- If asked something you don't know say to contact the team directly
- If the user writes in Luganda reply in Luganda
- If the user writes in English reply in English
- Always end by offering to help further
- Never make up information about the company
- Payment accepted via MTN Mobile Money, Airtel Money, bank transfer"""


def get_ai_response(user_message, lang="en"):
    """Get intelligent response from Google Gemini API (Free)"""

    if not GEMINI_API_KEY:
        if lang == "lg":
            return "Nkwetaagisa obuyambi. Yita ku +256 700 000000 oba ddamu *menu*."
        return "Let me connect you with our team. Call +256 700 000000 or reply *menu*."

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

        headers = {"Content-Type": "application/json"}

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{SYSTEM_PROMPT}\n\nUser message: {user_message}"
                        }
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 300,
                "temperature": 0.7
            }
        }

        response = requests.post(url, headers=headers, json=payload, timeout=15)

        if response.status_code == 200:
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            raise Exception(f"Gemini API error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Gemini API error: {e}")
        if lang == "lg":
            return "Nkwetaagisa obuyambi. Yita ku +256 700 000000."
        return "Let me connect you with our team. Call +256 700 000000 or WhatsApp us directly."
