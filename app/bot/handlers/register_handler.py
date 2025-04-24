import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from app.models.models import Skill, SkillType
from app.services.survey_service import save_user_skill, save_user_skill_by_question_key

survey = [
    {
        "question": "¿Qué lenguaje de programación dominas más?",
        "key": "language",
        "options": ["Python", "Java", "JavaScript", "PHP", "C#"]
    },
    {
        "question": "¿Qué framework dominas más?",
        "key": "framework",
        "options": ["Django", "SpringBoot", "React, Angular, Node.js, Express, Vue, etc.", "Laravel"]
    }
]

skill_mapping = {
    "language": SkillType.LANGUAGE,
    "framework": SkillType.FRAMEWORK,
}

# Dictionary for saving responses
user_survey_progress = {}

async def registro_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_survey_progress[chat_id] = {"current": 0, "answers": {}}
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
    await context.bot.send_message(chat_id=chat_id, text=q["question"], reply_markup=reply_markup)

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

        # Guardar en base de datos
        try:
            skill_type = skill_mapping.get(key)
            if skill_type:
                telegram_username = query.from_user.username
                await save_user_skill_by_question_key(telegram_username, key, value, update_existing=True)
        except Exception as e:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Error guardando la respuesta: {e}")

        await send_next_question(chat_id, context)