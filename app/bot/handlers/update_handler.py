from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatType
from app.bot.handlers.register_handler import send_next_question, user_survey_progress
from app.services.survey_service import save_user_skill_by_question_key
from app.models.models import User

async def actualizar_habilidades_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    gemini

    if chat.type != ChatType.PRIVATE:
        await update.message.reply_text("❗ Este comando sólo puede usarse desde un chat privado.")
        return

    # Verify if user exists in DB
    if not (user := await User.get_or_none(id=user_id)):
        await update.message.reply_text(
            "❗No estás registrado en el sistema. Utiliza el comando /registro para registrarte."
        )
        return

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
            user_id = query.from_user.id
            #mode = user_data.get("mode", "register")
            print("SE UTILIZO EL SURVEY2")
            await save_user_skill_by_question_key(user_id, key, value, update_existing=True)
        except Exception as e:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Error guardando la respuesta: {e}")

        await send_next_question(chat_id, context)