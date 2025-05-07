from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from app.services.gemini_service import classify_intent
from app.bot.handlers.update_handler import actualizar_habilidades_command

async def handle_natural_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Verify private chat
    if update.message.chat.type != "private":
        return

    user_message = update.message.text.strip()
    intent = await classify_intent(user_message)

    # Start flow if intent is detected
    if intent == "actualizar_habilidades":
        await actualizar_habilidades_command(update, context)
    else:
        await update.message.reply_text("❌ No entendí tu solicitud. Usa /actualizar_habilidades o /ayuda.")