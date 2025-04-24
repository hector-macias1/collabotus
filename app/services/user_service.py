from tortoise.exceptions import IntegrityError
from tortoise.transactions import in_transaction

from app.models.models import User, Skill, UserSkill, SubscriptionType, UserCreate_Pydantic
from app.models.models import UserCreate_Pydantic  # Schema Pydantic para validación
from typing import Optional, List


class UserService:
    @staticmethod
    async def create_or_update_user(telegram_id: str, username: str, first_name: str) -> User:
        user, created = await User.get_or_create(
            id=telegram_id,
            defaults={
                'telegram_usr': username,
                'first_name': first_name,
                'subscription_type': SubscriptionType.FREE.value
            }
        )
        if not created:
            user.telegram_usr = username
            user.first_name = first_name
            await user.save()
        return user

    @staticmethod
    async def update_user_skills(telegram_id: str, skills_data: List[dict]) -> User:
        user = await User.get(id=telegram_id).prefetch_related('skills')

        # Procesar habilidades
        for skill_info in skills_data:
            skill_type = skill_info['type']
            skill_name = skill_info['name']
            skill_value = skill_info['value']

            # Crear o obtener habilidad
            skill, _ = await Skill.get_or_create(
                name=skill_name,
                defaults={'type': skill_type}
            )

            # Actualizar relación usuario-habilidad
            await UserSkill.update_or_create(
                user=user,
                skill=skill,
                defaults={'value': skill_value}
            )

        return await user.fetch_related('skills')

    @staticmethod
    async def complete_registration(telegram_id: str, survey_data: dict) -> User:
        # Validar datos con Pydantic
        user_data = UserCreate_Pydantic(**survey_data)

        async with in_transaction():
            user = await UserService.create_or_update_user(
                telegram_id=telegram_id,
                username=user_data.username,
                first_name=user_data.first_name
            )

            await UserService.update_user_skills(
                telegram_id=telegram_id,
                skills_data=user_data.skills
            )

        return user