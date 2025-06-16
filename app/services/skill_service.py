from typing import Dict, List, Tuple, Any

from fastapi import HTTPException
from tortoise.exceptions import DoesNotExist

from app.models.models import UserSkill, Project, ProjectUser
from app.models.models import UserSkill_Pydantic, UserSkillCreate_Pydantic


class SkillService:
    @staticmethod
    async def list_by_project(project_id: int) -> List[UserSkill]:
        # Verify if project exists
        if not await Project.filter(id=project_id).exists():
            raise DoesNotExist(f"Project with id={project_id} not found")
        # Filter UserSkill where user is related with the project
        qs = UserSkill.filter(user__projects__id=project_id).prefetch_related("user", "skill")
        return await qs

    @staticmethod
    async def get_user_skills_by_project(project_id: int) -> dict:
        # Verify if project exists
        project = await Project.get_or_none(id=project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get all project members with their skills prefetched
        project_users = await ProjectUser.filter(project=project).prefetch_related(
            'user__user_skills__skill'
        )

        skills_by_user = {}
        for pu in project_users:
            user = pu.user
            user_skills = user.user_skills  # Preloaded with fetch

            skills_dict = {}
            for us in user_skills:
                skill_name = us.skill.name
                try:
                    skill_value = int(us.value)  # Convert to int if possible
                except ValueError:
                    skill_value = us.value  # Keep as string if failed

                skills_dict[skill_name] = skill_value

            # Use first_name as key (could be username if available)
            skills_by_user[user.id] = skills_dict

        return skills_by_user

    @staticmethod
    async def fetch_all_user_skills() -> Dict[int, List[Tuple[str,int]]]:
        """
        Returns a dict user_id → list of (skill_name, valor)
        """
        skills = await UserSkill.all().prefetch_related("skill")
        result: Dict[int, List[Tuple[str,int]]] = {}
        for us in skills:
            result.setdefault(us.user.id, []).append((us.skill.name, us.value))
        return result