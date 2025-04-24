from telegram import Update
from telegram.ext import ContextTypes
from app.bot.handlers.register_handler import send_next_question, user_survey_progress
from app.services.survey_service import save_user_skill_by_question_key

async def actualizar_habilidades_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_survey_progress[chat_id] = {
        "current": 0,
        "answers": {},
        "mode": "update"  # modo que indica actualización en lugar de registro nuevo
    }
    await context.bot.send_message(chat_id=chat_id, text="🔄 Vamos a actualizar tus habilidades.")
    await send_next_question(chat_id, context)

async def handle_survey_response2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    data = query.data  # "key|value"
    key, value = data.split("|")

    user_data = user_survey_progress.get(chat_id)
    if user_data:
        user_data["answers"][key] = value
        user_data["current"] += 1

        try:
            telegram_username = query.from_user.username
            #mode = user_data.get("mode", "register")
            await save_user_skill_by_question_key(telegram_username, key, value, update_existing=True)
        except Exception as e:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Error guardando la respuesta: {e}")

        await send_next_question(chat_id, context)