from typing import List, Optional
from fastapi import HTTPException, status
from tortoise.exceptions import DoesNotExist, IntegrityError
from tortoise.transactions import in_transaction
from app.models.models import (
    User,
    Project,
    ProjectUser,
    ProjectStatus,
    ProjectRole,
    SubscriptionType,
)
from app.models.models import ProjectCreate_Pydantic, Project_Pydantic


class ProjectService:
    @staticmethod
    async def create_project(telegram_user_id: str, project_data: ProjectCreate_Pydantic) -> Project_Pydantic:
        """
        Create a new project with all required validations
        """
        async with in_transaction():
            try:
                # 1. Validar usuario creador
                creator = await User.get(usr_telegram=telegram_user_id)

                # 2. Validar límite de proyectos para Free
                if creator.subscription_type == SubscriptionType.FREE:
                    admin_projects = await ProjectUser.filter(
                        user=creator,
                        role=ProjectRole.ADMIN
                    ).count()
                    if admin_projects >= 1:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Free users can only create one project"
                        )

                # 3. Crear proyecto base
                project = await Project.create(
                    name=project_data.name,
                    description=project_data.description,
                    telegram_chat_id=project_data.telegram_chat_id,
                )

                # 4. Asignar creador como ADMIN
                await ProjectUser.create(
                    project=project,
                    user=creator,
                    role=ProjectRole.ADMIN
                )

                # 5. Validar y agregar miembros iniciales
                if project_data.initial_members:
                    await ProjectService._add_members_with_validation(
                        project=project,
                        members=project_data.initial_members
                    )

                return await Project_Pydantic.from_tortoise_orm(project)

            except IntegrityError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Database error: {str(e)}"
                )

    @staticmethod
    async def _add_members_with_validation(project: Project, members: List[str]):
        """
        Internal method for adding members with validation
        """
        for telegram_id in members:
            user = await User.get_or_none(usr_telegram=telegram_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {telegram_id} not registered"
                )

            # Evitar duplicados
            if not await ProjectUser.exists(project=project, user=user):
                await ProjectUser.create(
                    project=project,
                    user=user,
                    role=ProjectRole.MEMBER
                )

    @staticmethod
    async def get_project(project_id: int) -> Project_Pydantic:
        """
        Gets all the project's related data in one go
        """
        project = await Project.get_or_none(id=project_id).prefetch_related(
            "members",
            "tasks",
            "project_users__user"
        )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        return await Project_Pydantic.from_tortoise_orm(project)

    @staticmethod
    async def update_project_status(project_id: int, new_status: ProjectStatus) -> Project_Pydantic:
        """
        Update project status (only ADMIN)
        """
        project = await Project.get_or_none(id=project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        project.status = new_status
        await project.save()
        return await Project_Pydantic.from_tortoise_orm(project)

    @staticmethod
    async def add_project_member(project_id: int, telegram_id: str, role: ProjectRole = ProjectRole.MEMBER):
        """
        Adding a member to a project with validation of registration
        """
        async with in_transaction():
            # Validar existencia de usuario
            user = await User.get_or_none(usr_telegram=telegram_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not registered"
                )

            # Validar proyecto
            project = await Project.get_or_none(id=project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            # Validar rol único de ADMIN
            if role == ProjectRole.ADMIN:
                existing_admin = await ProjectUser.filter(
                    project=project,
                    role=ProjectRole.ADMIN
                ).exists()

                if existing_admin:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Project already has an admin"
                    )

            # Crear relación
            await ProjectUser.create(
                project=project,
                user=user,
                role=role
            )

            return {"message": "Member added successfully"}

    @staticmethod
    async def get_projects_by_user(telegram_id: str) -> List[Project_Pydantic]:
        """
        Getss all the projects of a user with their role
        """
        user = await User.get_or_none(usr_telegram=telegram_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        projects = await ProjectUser.filter(user=user).prefetch_related(
            "project",
            "project__tasks"
        )

        return [await Project_Pydantic.from_tortoise_orm(p.project) for p in projects]