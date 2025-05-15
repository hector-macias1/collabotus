import json
import re
import json

from app.config import Settings
from app.services.gemini_service import GeminiService
from app.utils.load_prompt import LoadPrompt

async def extract_project_data(text: str) -> dict:
    llm = GeminiService(Settings.GEMINI_KEY, Settings.LLM_MODEL)

    prompt = LoadPrompt.load_prompt("app/services/prompts/params.txt")
    #print("\n\n\n\n\n\nPROMPT FOR PARAMS: ", prompt.format(user_message=text))
    response = await llm.detect_intent(text=prompt, intent_prompt=text)
    #print("RESPONSE FOR PARAMS: ", (str(response)))
    #print(response)
    #print("JSON FINAL: ", json.loads(str(response)))
    return json.loads(str(response))