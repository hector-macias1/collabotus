from tortoise.exceptions import DoesNotExist
from tortoise.transactions import atomic

from app.models.models import User, Skill, UserSkill, SkillType
"""from app.models.models import (
    User, Skill, UserSkill, SkillType,
    UserSkill_Pydantic, UserSkillCreate_Pydantic
)"""

async def save_user_skill(user_id: int, skill_type: SkillType, skill_value: str):
    try:
        user = await User.get(id=user_id)
        print(User.all())
    except DoesNotExist:
        raise ValueError(f"Usuario con user_id={user_id} no encontrado")

    # Search or create skill in DB catalog
    skill, _ = await Skill.get_or_create(name=skill_type, defaults={"type": skill_type})

    # Save relation in UserSkill
    await UserSkill.create(user=user, skill=skill, value=skill_value)

QUESTION_KEY_TO_TYPE = {
    "language": SkillType.LANGUAGE,
    "framework": SkillType.FRAMEWORK,
    "database": SkillType.DATABASE,
    "prototyping": SkillType.PROTOTYPING,
    "agile": SkillType.AGILE,
    "requirements": SkillType.REQUIREMENTS,
    "documentation": SkillType.DOCUMENTATION,
    "testing": SkillType.TESTING,
    "devops": SkillType.DEVOPS,
}

async def save_user_skill_by_question_key(user_id: int, question_key: str, skill_name: str, update_existing: bool = True):
    try:
        user = await User.get(id=user_id)
    except DoesNotExist:
        raise ValueError(f"Usuario con user_id={user_id} no encontrado")

    print(question_key)
    skill_type = QUESTION_KEY_TO_TYPE.get(question_key)
    if not skill_type:
        raise ValueError(f"No se pudo determinar el tipo de skill para la clave: {question_key}")

    try:
        skill = await Skill.get(type=skill_type, name=skill_type)
        #print(skill)
    except DoesNotExist:
        raise ValueError(f"Skill '{skill_name}' con tipo '{skill_type.value}' no encontrado")

    if update_existing:
        existing = await UserSkill.filter(user=user, skill__type=skill_type).first()
        if existing:
            existing.skill = skill
            existing.value = skill_name
            await existing.save()
            return

    await UserSkill.create(user=user, skill=skill, value=skill_name)

"""
class SurveyService:
    @staticmethod
    @atomic()
    async def save_user_skill(
            telegram_username: str,
            skill_type: SkillType,
            skill_value: str
    ) -> UserSkill_Pydantic:
        # Convert Enums to string values if it's a dictionary
        try:
            user = await User.get(telegram_usr=telegram_username)
        except DoesNotExist:
            raise ValueError(f"Usuario con telegram_usr={telegram_username} no encontrado")
"""

