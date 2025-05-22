# app/bot/handlers/jobs.py
from datetime import datetime, timezone
from app.models.models import Task, TaskStatus


async def check_overdue_tasks(context):
    now = datetime.now(timezone.utc)

    # Obtener tareas vencidas no completadas
    overdue_tasks = await Task.filter(
        deadline__lt=now
    ).exclude(
        status=TaskStatus.DONE
    ).prefetch_related('project')

    for task in overdue_tasks:
        try:
            chat_id = int(task.project.telegram_chat_id)
            formatted_deadline = task.deadline.astimezone(timezone.utc).strftime('%d/%m/%Y %H:%M PST')

            mensaje = (
                f"⚠️ *Tarea atrasada:* {task.name}\n\n"
                f"📅 _Vencimiento:_ {formatted_deadline}\n\n"
                f"🔧 _Estado actual:_ {task.status.value.capitalize()}"
            )

            await context.bot.send_message(
                chat_id=chat_id,
                text=mensaje,
                parse_mode="Markdown"
            )

        except Exception as e:
            print(f"Error en tarea {task.id}: {str(e)}")