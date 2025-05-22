# Añadir estos estados al principio del archivo
from datetime import datetime

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters

from app.models.models import ProjectStatus, TaskStatus
from app.services.project_service import ProjectService
from app.services.task_service import TaskService

ACTUALIZAR_TAREA_STATES = range(4)
(
    SELECT_TASK,
    CHOOSE_OPERATION,
    UPDATE_STATUS,
    UPDATE_DEADLINE,
) = ACTUALIZAR_TAREA_STATES


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

    # Obtener tareas del usuario en este proyecto
    tasks = await TaskService.get_tasks_by_user_and_project(user.id, project.id)
    if not tasks:
        await update.message.reply_text("❗ No tienes tareas asignadas en este proyecto")
        return ConversationHandler.END

    context.user_data.clear()
    context.user_data["project_id"] = project.id
    context.user_data["user_id"] = user.id

    # Listar tareas
    tasks_list = "\n".join([
                               f"• {task.custom_id}: {task.name} (Estado: {TaskStatus(task.status).name}, Fecha límite: {task.deadline.strftime('%Y-%m-%d %H:%M')})"
                               for task in tasks])
    await update.message.reply_text(
        f"📝 Tus tareas asignadas:\n{tasks_list}\n"
        "Por favor, escribe el ID de la tarea que deseas actualizar:"
    )
    return SELECT_TASK


async def handle_task_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_custom_id = update.message.text.strip()
    project_id = context.user_data["project_id"]
    user_id = context.user_data["user_id"]

    # Validar tarea
    task = await TaskService.get_task_by_custom_id_and_project(task_custom_id, project_id, user_id)
    if not task:
        await update.message.reply_text("❌ ID de tarea inválido. Intenta de nuevo:")
        return SELECT_TASK

    context.user_data["task"] = {
        "id": task.id,
        "custom_id": task.custom_id,
        "name": task.name,
        "current_status": task.status,
        "current_deadline": task.deadline
    }

    await update.message.reply_text(
        "¿Qué operación deseas realizar?\n"
        "1. Cambiar estado de la tarea\n"
        "2. Extender fecha límite\n"
        "3. Cancelar proceso"
    )
    return CHOOSE_OPERATION


async def handle_operation_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()

    if choice == "1":
        await update.message.reply_text(
            "Selecciona el nuevo estado:\n"
            "1. En progreso (IN_PROGRESS)\n"
            "2. Terminada (DONE)\n"
            "3. Cancelar"
        )
        return UPDATE_STATUS
    elif choice == "2":
        await update.message.reply_text(
            "Introduce la nueva fecha límite (YYYY-MM-DD HH:MM):\n"
            "Ejemplo: 2024-12-31 23:59"
        )
        return UPDATE_DEADLINE
    elif choice == "3":
        await cancel_update(update, context)
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Opción inválida. Elige 1, 2 o 3:")
        return CHOOSE_OPERATION


async def handle_status_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()
    task_data = context.user_data["task"]

    if choice == "1":
        new_status = TaskStatus.IN_PROGRESS
    elif choice == "2":
        new_status = TaskStatus.DONE
    elif choice == "3":
        await cancel_update(update, context)
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Opción inválida. Elige 1, 2 o 3:")
        return UPDATE_STATUS

    # Actualizar estado
    await TaskService.update_task(
        task_id=task_data["id"],
        status=new_status
    )

    # Mensaje de confirmación
    await update.message.reply_text(
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
    await update.message.reply_text("🚫 Actualización cancelada")
    return ConversationHandler.END


def get_update_task_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler('actualizartarea', actualizartarea_command)],
        states={
            SELECT_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task_selection)],
            CHOOSE_OPERATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_operation_selection)],
            UPDATE_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_status_update)],
            UPDATE_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_deadline_update)],
        },
        fallbacks=[CommandHandler('cancelar', cancel_update)],
        allow_reentry=True
    )