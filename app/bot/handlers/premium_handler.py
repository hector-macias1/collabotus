import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ChatType

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage /start command"""
    chat = update.effective_chat
    chat_id = update.effective_chat.id

    if chat.type != ChatType.PRIVATE:
        await update.message.reply_text("❗ Este comando sólo puede usarse desde un chat privado.")
        return

    await update.message.reply_text("Para elevar tu cuenta a premium, sigue el siguiente enlace: \n")