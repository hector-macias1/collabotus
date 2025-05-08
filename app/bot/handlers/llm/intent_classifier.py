from app.services.gemini_service import GeminiService
import yaml
from typing import Dict

class IntentClassifier:
    def __init__(self, api_key: str, model: str):
        self.llm = GeminiService(api_key, model)
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> Dict[str, str]:
        with open("app/services/prompts/intents.yaml") as f:
            return yaml.safe_load(f)

    async def classify(self, text: str) -> str:
        print("NUEVA VERSION: ")
        for intent, prompt in self.prompts.items():
            result = await self.llm.detect_intent(text=prompt, intent_prompt=text)
            if result == intent:
                print("RESULT: ", result)
                return intent
        return "otras"