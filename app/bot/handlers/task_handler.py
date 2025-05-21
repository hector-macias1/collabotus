from datetime import datetime
from telegram import Update, Chat
from telegram.constants import ChatType
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, ConversationHandler, filters

from app.config import Settings
from app.models.models import TaskStatus, TaskCreate_Pydantic, Task, Project, User
from app.services.gemini_service import GeminiService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.services.project_service import ProjectService
from app.models.models import ProjectStatus
from app.services.user_service import UserService

# States
TASK_ID, TASK_NAME, TASK_DESC, TASK_DEADLINE = range(4)


async def agregar_tarea_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    # Verificar si es grupo
    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await update.message.reply_text("❗ Este comando solo puede usarse en grupos.")
        return ConversationHandler.END

    # Verify active project
    project = await ProjectService.get_project_by_chat_id(str(chat.id))
    if not project or project.status == ProjectStatus.TERMINATED:
       await update.message.reply_text("❌ No hay proyecto activo en este grupo")
       return ConversationHandler.END

    context.user_data.clear()
    context.user_data["task_data"] = {}

    await update.message.reply_text("📝 Por favor, envía el identificador de la tarea:")
    return TASK_ID


async def handle_task_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["task_data"]["identifier"] = update.message.text.strip()
    await update.message.reply_text("🔤 Ahora el nombre de la tarea:")
    return TASK_NAME


async def handle_task_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["task_data"]["name"] = update.message.text.strip()
    await update.message.reply_text("📄 Descripción de la tarea:")
    return TASK_DESC


async def handle_task_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["task_data"]["description"] = update.message.text.strip()
    await update.message.reply_text(
        "⏰ Fecha límite (YYYY-MM-DD HH:MM):\n"
        "Ejemplo: 2024-12-31 18:00"
    )
    return TASK_DEADLINE


async def handle_task_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        deadline = datetime.strptime(text, "%Y-%m-%d %H:%M")
    except ValueError:
        await update.message.reply_text("⚠ Formato inválido. Intenta de nuevo:")
        return TASK_DEADLINE  # Stay in the same state

    task_data = context.user_data["task_data"]
    task_data["deadline"] = deadline

    # Save
    try:
        project = await ProjectService.get_project_by_chat_id(str(update.effective_chat.id))
        print(project)
        task, created = await Task.get_or_create(
            custom_id=task_data["identifier"],
            name=task_data["name"],
            description=task_data["description"],
            deadline=deadline,
            project_id=project.id,
        )

        llm = GeminiService(Settings.GEMINI_KEY, Settings.LLM_MODEL)

        user_to_assign = await UserService.get_user_by_id(
            await llm.assign_task(project.id, task.name, task.description)
        )

        await TaskService.assign_user(task.id, user_to_assign.id)

        await update.message.reply_text(
            f"✅ Tarea creada:\n"
            f"ID: {task_data['identifier']}\n"
            f"Nombre: {task_data['name']}\n"
            f"Deadline: {deadline.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"Asginada a: @{user_to_assign.first_name}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

    context.user_data.clear()
    return ConversationHandler.END


async def cancel_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🚫 Operación cancelada")
    return ConversationHandler.END

def get_task_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler('agregartarea', agregar_tarea_command)],
        states={
            TASK_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task_id)],
            TASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task_name)],
            TASK_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task_desc)],
            TASK_DEADLINE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    handle_task_deadline
                )
            ]
        },
        fallbacks=[CommandHandler('cancelar', cancel_task)],
        allow_reentry=True
    )

async def listar_tareas_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type != ChatType.GROUP and chat.type != ChatType.SUPERGROUP:
        await update.message.reply_text("❗ Este comando solo puede usarse desde un chat grupal.")
        return

    project = await ProjectService.get_project_by_chat_id(str(chat.id))
    tasks = await TaskService.get_tasks_by_project(project.id)

    if not tasks:
        await update.message.reply_text(
            "❗ No hay ninguna tarea en el proyecto\nPuedes crear una usando el comando /agregartarea."
        )
        return

    tasks_string = ''

    for task in tasks:
        tasks_string += f'{task.custom_id}: {task.name}\n'

    await update.message.reply_text("Tareas:\n" + tasks_string)