# app/bot/handlers/jobs.py
from datetime import datetime, timezone

from app.config import Settings
from app.models.models import Task, TaskStatus, ProjectUser, User
from app.services.gemini_service import GeminiService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService


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
            print("FIRST FLAG")
            project_users = await ProjectService.get_project_members(task.project.id)
            tasks = await TaskService.get_tasks_by_project(task.project.id)
            assigned_user = await TaskService.get_user_by_task(task.id)
            print("SECOND FLAG")
            assigned_tasks = ''
            for tk in tasks:
                assigned_tasks += f"User {await TaskService.get_user_by_task(tk.id)} - Task {tk.custom_id} {tk.name} {tk.deadline}\n"

            print("THIRD FLAG")
            # Construir contexto para la IA
            context_ai = {
                "custom_id": task.custom_id,
                "task_name": task.name,
                "deadline": task.deadline.strftime('%d/%m/%Y %H:%M'),
                "project_name": task.project.name,
                "assigned_user": assigned_user,
                "current_status": task.status.value,
                "team_members": project_users,
                "all_project_tasks": assigned_tasks,
            }
            print("FORUTH FLAG")
            llm = GeminiService(Settings.GEMINI_KEY, Settings.LLM_MODEL)

            print("FIFTH FLAG")
            notification = await llm.solve_overdue_task(context_ai)

            print("SEVENTH FLAG")
            await context.bot.send_message(
                chat_id=chat_id,
                text=notification,
                parse_mode="Markdown"
            )

        except Exception as e:
            print(f"Error en tarea {task.id}: {str(e)}")


            """
            mensaje = (
                f"⚠️ *Tarea atrasada:* {task.name}\n\n"
                f"📅 _Vencimiento:_ {formatted_deadline}\n\n"
                f"🔧 _Estado actual:_ {task.status.value.capitalize()}"
            )

            user = await TaskService.get_user_by_task(task.id)

            print("Tarea asignada a: ", user)



            project_users = await ProjectService.get_project_members(task.project.id)

            print("Miembros del proyecto: ", project_users)

            tasks = await TaskService.get_tasks_by_project(task.project.id)
            print("Tareas del proyecto: ", tasks)

            users_tasks = ''
            for tk in tasks:
                users_tasks += f"User {await TaskService.get_user_by_task(tk.id)} - Task {tk.custom_id} {tk.name}\n"

            print(users_tasks)
            await context.bot.send_message(
                chat_id=chat_id,
                text=mensaje,
                parse_mode="Markdown"
            )

        except Exception as e:
            print(f"Error en tarea {task.id}: {str(e)}")"""
