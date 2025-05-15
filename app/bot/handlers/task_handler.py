from telegram import Update, Chat
from telegram.constants import ChatType
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from app.models.models import TaskStatus, TaskCreate_Pydantic, Task
from app.services.project_service import ProjectService
from app.services.task_service import TaskService

async def agregar_tarea_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user_id = update.effective_user.id

    if chat.type != ChatType.GROUP and chat.type != ChatType.SUPERGROUP:
        await update.message.reply_text("❗ Este comando solo puede usarse desde un chat grupal.")
        return

    project = await ProjectService.get_project_by_chat_id(str(chat.id))
    if not project:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"No tienes ningun proyecto en este chat.\nPuedes crear uno usando el comando /crear_proyecto.",
            parse_mode="Markdown"
        )
        return

