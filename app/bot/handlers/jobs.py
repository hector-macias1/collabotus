# app/bot/handlers/jobs.py
from datetime import datetime, timezone

from app.config import Settings
from app.models.models import Task, TaskStatus, ProjectUser, User
from app.services.gemini_service import GeminiService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService


async def check_overdue_tasks(context):
    now = datetime.now(timezone.utc)

    # Get non completed overdue tasks
    overdue_tasks = await Task.filter(
        deadline__lt=now
    ).exclude(
        status=TaskStatus.DONE
    ).prefetch_related('project')

    for task in overdue_tasks:
        try:
            chat_id = int(task.project.telegram_chat_id)
            formatted_deadline = task.deadline.astimezone(timezone.utc).strftime('%d/%m/%Y %H:%M PST')

            project_users = await ProjectService.get_project_members(task.project.id)
            tasks = await TaskService.get_tasks_by_project(task.project.id)
            assigned_user = await TaskService.get_user_by_task(task.id)

            assigned_tasks = ''
            for tk in tasks:
                assigned_tasks += f"""
                User {await TaskService.get_user_by_task(tk.id)} - Task {tk.custom_id} {tk.name} {tk.deadline}\n
                """

            # Build context for AI service
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

            llm = GeminiService(Settings.GEMINI_KEY, Settings.LLM_MODEL)
            notification = await llm.solve_overdue_task(context_ai)

            await context.bot.send_message(
                chat_id=chat_id,
                text=notification,
                parse_mode="Markdown"
            )

        except Exception as e:
            print(f"Error in task {task.id}: {str(e)}")