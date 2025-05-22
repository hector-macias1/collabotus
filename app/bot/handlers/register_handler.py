import logging
from telegram.constants import ChatType
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from app.models.models import Skill, SkillType, User
from app.services.survey_service import save_user_skill, save_user_skill_by_question_key

survey = [
    {
        "question": "¿Qué lenguaje de programación dominas más?",
        "key": "language",
        "options": ["Python", "Java", "JavaScript", "PHP", "C#", 'C/C++']
    },
    {
        "question": "¿Qué framework dominas más?",
        "key": "framework",
        "options": ["Django", "SpringBoot", "React, Angular, Node.js, Express, Vue, etc.", "Laravel", '.NET']
    },
    {
        "question": "¿Cómo calificas tu dominio en bases de datos (sql/nosql)?\n1: Básico - 5: Experto",
        "key": "database",
        "options": ["1", "2", "3", "4", "5"]
    },
    {
        "question": "¿Cómo calificas tu dominio en herramientas de prototipado (Figma, Uizard, etc.)?\n1: Básico - 5: Experto",
        "key": "prototyping",
        "options": ["1", "2", "3", "4", "5"]
    },
    {
        "question": "¿Cómo calificas tu dominio en metodologías ágiles?\n1: Básico - 5: Experto",
        "key": "agile",
        "options": ["1", "2", "3", "4", "5"]
    },
    {
        "question": "¿Cómo calificas tu dominio en levantamiento de requerimientos?\n1: Básico - 5: Experto",
        "key": "requirements",
        "options": ["1", "2", "3", "4", "5"]
    },
    {
        "question": "¿Cómo calificas tu dominio en documentación técnica?\n1: Básico - 5: Experto",
        "key": "documentation",
        "options": ["1", "2", "3", "4", "5"]
    },
    {
        "question": "¿Cómo calificas tu dominio en testing/QA (unit testing, herramientas como Selenium)?\n1: Básico - 5: Experto",
        "key": "testing",
        "options": ["1", "2", "3", "4", "5"]
    },
    {
        "question": "¿Cómo calificas tu dominio en DevOps (CI/CD, Docker, plataformas cloud)?\n1: Básico - 5: Experto",
        "key": "devops",
        "options": ["1", "2", "3", "4", "5"]
    }
]

skill_mapping = {
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

# Dictionary for saving responses
user_survey_progress = {}

async def registro_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat.type != ChatType.PRIVATE:
        await update.message.reply_text("❗ Este comando sólo puede usarse desde un chat privado.")
        return

    # Verify if user exists in DB
    if user := await User.get_or_none(id=user_id):
        await update.message.reply_text(
            "❗Ya estás registrado en el sistema.\nUtiliza el comando /actualizar_habilidades para actualizar tu información."
        )
        return

    user_survey_progress[chat_id] = {"current": 0, "answers": {}}

    print("USER ID: ", update.effective_user.id)
    print("USERNAME: ", update.effective_user.username)
    print("FIRST NAME: ", update.effective_user.first_name)

    _user, created = await User.get_or_create(
        id=update.effective_user.id,
        username=update.effective_user.username.lower(),
        first_name=update.effective_user.first_name
    )

    await context.bot.send_message(
        chat_id=chat_id,
        text="Vamos a registrar tus habilidades."
    )
    await send_next_question(chat_id, context)

async def send_next_question(chat_id, context):
    user_data = user_survey_progress.get(chat_id)
    if user_data is None:
        return

    current_index = user_data["current"]
    if current_index >= len(survey):
        # End survey
        answers = user_data["answers"]
        summary = "\n".join([f"{k}: {v}" for k, v in answers.items()])
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ ¡Gracias! Aquí están tus respuestas:\n\n{summary}"
        )
        del user_survey_progress[chat_id]
        return

    q = survey[current_index]
    buttons = [
        [InlineKeyboardButton(opt, callback_data=f"{q['key']}|{opt}")]
        for opt in q["options"]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await context.bot.send_message(
        chat_id=chat_id,
        text=q["question"],
        reply_markup=reply_markup
    )

async def handle_survey_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    data = query.data  # Format: "key|answer"
    key, value = data.split("|")

    user_data = user_survey_progress.get(chat_id)
    if user_data:
        user_data["answers"][key] = value
        user_data["current"] += 1

        # Save in db
        try:
            skill_type = skill_mapping.get(key)
            if skill_type:
                user_id = query.from_user.id
                await save_user_skill_by_question_key(user_id, key, value, update_existing=True)
        except Exception as e:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Error guardando la respuesta: {e}"
            )

        await send_next_question(chat_id, context)