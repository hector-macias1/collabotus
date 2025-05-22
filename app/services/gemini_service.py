import logging
import google.genai as genai
from typing import Optional
from typing import Dict, Any

from app.config import settings
from app.services.skill_service import SkillService
from app.utils.load_prompt import LoadPrompt


class GeminiService:
    def __init__(self, api_key: str, model: str):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    async def detect_intent(self, text: str, intent_prompt: str) -> Optional[str]:
        try:
            print("WILL PROCESS THE RESPONSE FOR THIS PROMPT: ", text.format(user_message=intent_prompt))
            response = self.client.models.generate_content(
                model=self.model,
                contents=text.format(user_message=intent_prompt)
            )
            print("RESPONSE: ", response.text)
            return response.text.strip().lower()
        except Exception as e:
            logging.error(f"Gemini Service ERROR: {e}")
            return None

    async def assign_task(self, project_id:int, task_title: str, task_desc: str) -> Optional[int]:
        text = LoadPrompt.load_prompt("app/services/prompts/assignation.txt")
        users = await SkillService.get_user_skills_by_project(project_id)
        print(text)
        print(text.format(task_title=task_title, task_description=task_desc, users=users))

        try:
            prompt = text.format(task_title=task_title, task_description=task_desc, users=users)
            print("WILL PROCESS THE RESPONSE FOR THIS PROMPT: ", prompt)
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            print("RESPONSE: ", response.text)
            return int(response.text.strip().lower())
        except Exception as e:
            logging.error(f"Gemini Service ERROR: {e}")
            return None

    async def solve_overdue_task(self, context) -> Optional[str]:
        text = LoadPrompt.load_prompt("app/services/prompts/notify.txt")
        print(text)

        prompt = text.format(
            custom_id=context['custom_id'],
            task_name=context['task_name'],
            deadline=context['deadline'],
            project_name=context['project_name'],
            assigned_user=context['assigned_user'],
            current_status=context['current_status'],
            team_members=context['team_members'],
            all_project_tasks=context['all_project_tasks']
        )
        print("WILL PROCESS THE RESPONSE FOR THIS PROMPT: ", prompt)
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )
        print("RESPONSE: ", response.text)
        return response.text
