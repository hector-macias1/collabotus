from telegram import Update, Chat
from telegram.constants import ChatType
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from app.models.models import TaskStatus, TaskCreate_Pydantic, Task
from app.services.task_service import TaskService

# Save the user's progress in a dictionary:
user_project_creation = {}

async def agregar_tarea_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user_id = update.effective_user.id

    if chat.type != ChatType.GROUP and chat.type != ChatType.SUPERGROUP:
        await update.message.reply_text("❗ Este comando solo puede usarse desde un chat grupal.")
        return

    user_project_creation[user_id] = {
        "group_id": chat.id,
        "step": "ask_name"
    }