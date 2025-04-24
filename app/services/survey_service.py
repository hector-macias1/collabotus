from app.models.models import User, Skill, UserSkill, SkillType
from tortoise.exceptions import DoesNotExist

async def save_user_skill(telegram_username: str, skill_type: SkillType, skill_value: str):
    try:
        user = await User.get(telegram_usr=telegram_username)
    except DoesNotExist:
        raise ValueError(f"Usuario con telegram_usr={telegram_username} no encontrado")

    # Buscar o crear skill en el catálogo
    skill, _ = await Skill.get_or_create(name=skill_type, defaults={"type": skill_type})

    # Guardar relación en UserSkill
    await UserSkill.create(user=user, skill=skill, value=skill_value)

QUESTION_KEY_TO_TYPE = {
    "language": SkillType.LANGUAGE,
    "framework": SkillType.FRAMEWORK,
    # Agrega más si hay más tipos
}

async def save_user_skill_by_question_key(telegram_username: str, question_key: str, skill_name: str, update_existing: bool = True):
    try:
        user = await User.get(telegram_usr=telegram_username)
    except DoesNotExist:
        raise ValueError(f"Usuario con telegram_usr={telegram_username} no encontrado")

    skill_type = QUESTION_KEY_TO_TYPE.get(question_key)
    if not skill_type:
        raise ValueError(f"No se pudo determinar el tipo de skill para la clave: {question_key}")

    try:
        skill = await Skill.get(type=skill_type, name=skill_type)
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

