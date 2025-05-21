import re
from typing import Optional

from app.services.gemini_service import GeminiService
from app.services.skill_service import SkillService


class TaskAssigner:
    def __init__(self, gemini: GeminiService, skill_service: SkillService):
        self.gemini = gemini
        self.skill_service = skill_service

    async def assign(self, task_title: str, task_desc: str) -> Optional[int]:
        user_skills = await self.skill_service.fetch_all_user_skills()
        prompt = self._build_prompt(task_title, task_desc, user_skills)
        response = await self.gemini.client.models.generate_content(
            model=self.gemini.model,
            contents=prompt
        )
        # Se asume que Gemini devuelve algo como "El id es 2"
        match = re.search(r"\d+", response.text)
        return int(match.group(0)) if match else None

    @staticmethod
    def _build_prompt(self, title, desc, skills_dict):
        lines = [f"TAREA:\nTítulo: {title}\nDescripción: {desc}\n",
                 "USUARIOS DISPONIBLES:"]
        for uid, skills in skills_dict.items():
            skl_str = ", ".join(f"{s}:{v}" for s,v in skills)
            lines.append(f"- {uid}: {skl_str}")
        lines.append(
            "\nInstrucciones:\nElige el ID del usuario que mejor encaje con la tarea "
            "basándote en sus habilidades y devuelve solo el número."
        )
        return "\n".join(lines)