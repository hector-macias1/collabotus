import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage /start command"""
    chat_id = update.effective_chat.id

    await update.message.reply_text("Para elevar tu cuenta a premium, sigue el siguiente enlace: \n")