from typing import List, Optional, Union, Dict, Any, Tuple
from tortoise.exceptions import DoesNotExist
from tortoise.transactions import atomic

from app.models.models import (
    Project, User, ProjectUser, ProjectRole, ProjectStatus, Task,
    Project_Pydantic, ProjectCreate_Pydantic,
    ProjectUser_Pydantic, ProjectUserCreate_Pydantic,
    Task_Pydantic, TaskCreate_Pydantic
)
from app.models.models import TaskStatus

class TaskService:
    @staticmethod
    async def create_task(task_data: Union[Dict[str, Any], TaskCreate_Pydantic]) -> Task_Pydantic:
        task_obj = await Task.create(**task_data)
        return await Task_Pydantic.from_tortoise_orm(task_obj)

    @staticmethod
    async def get_task(task_id: int) -> Optional[Task_Pydantic]:
        try:
            task = await Task.get(id=task_id)
            return await Task_Pydantic.from_tortoise_orm(task)
        except DoesNotExist:
            return None

    @staticmethod
    async def update_task(task_id: int, update_data: dict) -> Optional[Task_Pydantic]:
        try:
            task = await Task.get(id=task_id)
            for field, value in update_data.items():
                setattr(task, field, value)
            await task.save()
            return await Task_Pydantic.from_tortoise_orm(task)
        except DoesNotExist:
            return None

    @staticmethod
    async def delete_task(task_id: int) -> bool:
        deleted_count = await Task.filter(id=task_id).delete()
        return deleted_count > 0

    @staticmethod
    async def get_tasks_by_project(project_id: int) -> List[Task_Pydantic]:
        tasks = await Task.filter(project_id=project_id).all()
        return await Task_Pydantic.from_queryset(tasks)

    @staticmethod
    async def get_tasks_by_user(user_id: int) -> List[Task_Pydantic]:
        tasks = await Task.filter(assigned_user_id=user_id).all()
        return await Task_Pydantic.from_queryset(tasks)

    @staticmethod
    async def assign_user(task_id: int, user_id: int) -> Optional[Task_Pydantic]:
        try:
            task = await Task.get(id=task_id)
            user = await User.get(id=user_id)
            task.assigned_user = user
            await task.save()
            return await Task_Pydantic.from_tortoise_orm(task)
        except DoesNotExist:
            return None

    @staticmethod
    async def change_status(task_id: int, status: TaskStatus) -> Optional[Task_Pydantic]:
        try:
            task = await Task.get(id=task_id)
            task.status = status
            await task.save()
            return await Task_Pydantic.from_tortoise_orm(task)
        except DoesNotExist:
            return None