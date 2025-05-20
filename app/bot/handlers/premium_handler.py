import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ChatType

from app.models.models import User

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage /start command"""
    chat = update.effective_chat
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat.type != ChatType.PRIVATE:
        await update.message.reply_text("❗ Este comando sólo puede usarse desde un chat privado.")
        return

    # Verify if user exists in DB
    if not (user := await User.get_or_none(id=user_id)):
        await update.message.reply_text(
            "❗No estás registrado en el sistema. Utiliza el comando /registro para registrarte."
        )
        return

    await update.message.reply_text("Para elevar tu cuenta a premium, sigue el siguiente enlace: \n")