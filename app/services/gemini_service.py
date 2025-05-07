import logging
import google.genai as genai
from typing import Optional
from typing import Dict, Any

from app.config import settings

class GeminiService:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=settings.GEMINI_KEY)
        self.model = settings.LLM_MODEL

    async def detect_intent(self, text: str, intent_prompt: str) -> Optional[str]:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=intent_prompt.format(user_message=text)
            )
            return response.text.strip().lower()
        except Exception as e:
            logging.error(f"Gemini Service ERROR: {e}")
            return None