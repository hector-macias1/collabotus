from tortoise.exceptions import IntegrityError, DoesNotExist
from tortoise.transactions import in_transaction

from app.models.models import User, Skill, UserSkill, SubscriptionType, UserCreate_Pydantic
from app.models.models import User_Pydantic, UserCreate_Pydantic  # Pydantic schema for validation
from typing import Optional, List


class UserService:
    @staticmethod
    async def create_or_update_user(telegram_id: int, username: str, first_name: str) -> User:
        user, created = await User.get_or_create(
            id=telegram_id,
            defaults={
                'username': username,
                'first_name': first_name,
                'subscription_type': SubscriptionType.FREE.value
            }
        )
        if not created:
            user.username = username
            user.first_name = first_name
            await user.save()
        return user

    @staticmethod
    async def get_user_by_id(user_id: int) -> Optional[User_Pydantic]:
        try:
            user = await User.get(id=user_id)
            print(user.id)
            return await User_Pydantic.from_tortoise_orm(user)
        except DoesNotExist:
            return None

    @staticmethod
    async def update_user_skills(telegram_id: int, skills_data: List[dict]) -> User:
        user = await User.get(id=telegram_id).prefetch_related('skills')

        # Process skills
        for skill_info in skills_data:
            skill_type = skill_info['type']
            skill_name = skill_info['name']
            skill_value = skill_info['value']

            # Create or get skill
            skill, _ = await Skill.get_or_create(
                name=skill_name,
                defaults={'type': skill_type}
            )

            # Update UserSkill relation
            await UserSkill.update_or_create(
                user=user,
                skill=skill,
                defaults={'value': skill_value}
            )

        return await user.fetch_related('skills')

    @staticmethod
    async def complete_registration(telegram_id: int, survey_data: dict) -> User:
        # Validate data with pydantic
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