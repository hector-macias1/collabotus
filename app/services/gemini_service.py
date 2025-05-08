import logging
import google.genai as genai
from typing import Optional
from typing import Dict, Any

from app.config import settings

class GeminiService:
    def __init__(self, api_key: str, model: str):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    async def detect_intent(self, text: str, intent_prompt: str) -> Optional[str]:
        try:
            ("SE VA A PROCESAR LA RESPUESTA DE ESTE PROMPT: ", text.format(user_message=intent_prompt))
            response = self.client.models.generate_content(
                model=self.model,
                contents=text.format(user_message=intent_prompt)
            )
            print("RESPUESTA: ", response)
            return response.text.strip().lower()
        except Exception as e:
            logging.error(f"Gemini Service ERROR: {e}")
            return None