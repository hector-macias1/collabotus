from datetime import datetime
from telegram import Update, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatType
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, ConversationHandler, filters, \
    CallbackQueryHandler

from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.models.models import ProjectStatus
from app.models.models import TaskStatus, TaskCreate_Pydantic, Task, Project, User

# Actualizar los estados
ACTUALIZAR_TAREA_STATES = range(3)
(SELECT_TASK, CHOOSE_OPERATION, UPDATE_DEADLINE) = ACTUALIZAR_TAREA_STATES


async def actualizartarea_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    # Verificar si es grupo
    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await update.message.reply_text("❗ Este comando solo puede usarse en grupos.")
        return ConversationHandler.END

    # Verificar proyecto activo
    project = await ProjectService.get_project_by_chat_id(str(chat.id))
    if not project or project.status == ProjectStatus.TERMINATED:
        await update.message.reply_text("❌ No hay proyecto activo en este grupo")
        return ConversationHandler.END

    # Obtener tareas y crear botones
    tasks = await TaskService.get_tasks_by_user_and_project(user.id, project.id)

    keyboard = [
        [InlineKeyboardButton(f"{task.custom_id}: {task.name}", callback_data=f"task_{task.id}")]
        for task in tasks
    ]
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel")])

    await update.message.reply_text(
        "📝 Selecciona una tarea:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECT_TASK


async def handle_task_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await cancel_update(update, context)
        return ConversationHandler.END

    task_id = int(query.data.split("_")[1])
    task = await TaskService.get_task_by_id(task_id)

    context.user_data["task"] = {
        "id": task.id,
        "custom_id": task.custom_id,
        "name": task.name,
        "current_status": task.status,
        "current_deadline": task.deadline
    }

    keyboard = [
        [InlineKeyboardButton("🔄 Cambiar estado", callback_data="change_status")],
        [InlineKeyboardButton("📅 Extender fecha", callback_data="extend_deadline")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
    ]

    await query.edit_message_text(
        f"Tarea seleccionada: {task.custom_id}\n¿Qué deseas hacer?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSE_OPERATION


async def handle_operation_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await cancel_update(update, context)
        return ConversationHandler.END

    if query.data == "change_status":
        keyboard = [
            [InlineKeyboardButton("En progreso", callback_data="status_IN_PROGRESS")],
            [InlineKeyboardButton("Terminada", callback_data="status_DONE")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")]
        ]

        await query.edit_message_text(
            "Selecciona el nuevo estado:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END  # Terminamos aquí porque es una operación directa

    if query.data == "extend_deadline":
        await query.edit_message_text(
            "Introduce la nueva fecha límite (YYYY-MM-DD HH:MM):\n"
            "Ejemplo: 2024-12-31 23:59\n"
            "O escribe /cancelar para abortar"
        )
        return UPDATE_DEADLINE
    return None


async def handle_status_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await cancel_update(update, context)
        return ConversationHandler.END

    new_status = TaskStatus[query.data.split("_")[1]]
    task_data = context.user_data["task"]

    await TaskService.update_task(
        task_id=task_data["id"],
        status=new_status
    )

    await query.edit_message_text(
        f"✅ Estado actualizado:\n"
        f"Tarea: {task_data['name']}\n"
        f"Estado anterior: {TaskStatus(task_data['current_status']).name}\n"
        f"Nuevo estado: {new_status.name}"
    )
    context.user_data.clear()
    return ConversationHandler.END


async def handle_deadline_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    task_data = context.user_data["task"]

    try:
        new_deadline = datetime.strptime(text, "%Y-%m-%d %H:%M")
    except ValueError:
        await update.message.reply_text("❌ Formato inválido. Intenta de nuevo:")
        return UPDATE_DEADLINE

    if new_deadline <= datetime.now():
        await update.message.reply_text("❌ La fecha debe ser futura. Intenta de nuevo:")
        return UPDATE_DEADLINE

    # Actualizar fecha
    await TaskService.update_task(
        task_id=task_data["id"],
        deadline=new_deadline
    )

    # Mensaje de confirmación
    await update.message.reply_text(
        f"✅ Fecha actualizada:\n"
        f"Tarea: {task_data['name']}\n"
        f"Fecha anterior: {task_data['current_deadline'].strftime('%Y-%m-%d %H:%M')}\n"
        f"Nueva fecha: {new_deadline.strftime('%Y-%m-%d %H:%M')}"
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    # Determinar si es un mensaje normal o un callback de botón inline
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("🚫 Actualización cancelada")
    else:
        await update.message.reply_text("🚫 Actualización cancelada")

    return ConversationHandler.END

def get_update_task_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler('actualizartarea', actualizartarea_command)],
        states={
            SELECT_TASK: [CallbackQueryHandler(handle_task_selection)],
            CHOOSE_OPERATION: [CallbackQueryHandler(handle_operation_selection)],
            UPDATE_DEADLINE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_deadline_update),
                CommandHandler('cancelar', cancel_update)
            ]
        },
        fallbacks=[CommandHandler('cancelar', cancel_update)],
        allow_reentry=True
    )