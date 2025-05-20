from typing import List, Optional, Union, Dict, Any, Tuple
from tortoise.exceptions import DoesNotExist
from tortoise.transactions import atomic

from app.models.models import (
    Project, User, ProjectUser, Task, ProjectRole, ProjectStatus,
    Project_Pydantic, ProjectCreate_Pydantic,
    ProjectUser_Pydantic, ProjectUserCreate_Pydantic
)


class ProjectService:
    """
    Service to manage operations related to projects.
    """

    @staticmethod
    async def get_project_by_id(project_id: int) -> Optional[Project_Pydantic]:
        """
        Gets a project by its ID.

        Args:
            project_id: Project ID

        Returns:
            Project details or None if not found
        """
        try:
            project = await Project.get(id=project_id)
            return await Project_Pydantic.from_tortoise_orm(project)
        except DoesNotExist:
            return None

    @staticmethod
    async def get_project_by_chat_id(chat_id: str) -> Optional[Project_Pydantic]:
        """
        Gets a project by its chatID.

        Args:
            project_id: Project ID

        Returns:
            Project details or None if not found
        """
        try:
            project = await Project.get(telegram_chat_id=chat_id)
            return await Project_Pydantic.from_tortoise_orm(project)
        except DoesNotExist:
            return None

    @staticmethod
    async def get_projects_by_user(user_id: int) -> List[Project_Pydantic]:
        """
        Gets all projects where a given user participates.

        Args:
            user_id: User ID to filter by.

        Returns:
            List of projects where the given user participates
        """
        user = await User.get(id=user_id)
        projects = await user.projects
        #print(projects)
        return [await Project_Pydantic.from_tortoise_orm(project) for project in projects]

    @staticmethod
    async def get_projects_by_status(status: Union[ProjectStatus, str]) -> List[Project_Pydantic]:
        """
        Gets all projects with a specific status.

        Args:
            status: Project status (can be ProjectStatus enum or a string)

        Returns:
            List of projects with the specified status.
        """
        # Manejar tanto objetos Enum como valores de string
        status_value = status.value if isinstance(status, ProjectStatus) else status
        projects = await Project.filter(status=status_value)
        return [await Project_Pydantic.from_tortoise_orm(project) for project in projects]

    @staticmethod
    async def get_user_role_in_project(user_id: int, project_id: int) -> Optional[ProjectRole]:
        """
        Gets the role of a user in a specific project.

        Args:
            user_id: User ID
            project_id: Project ID to filter by.

        Returns:
            User role in a specific project or None if the user is not in the project.
        """
        try:
            project_user = await ProjectUser.get(user_id=user_id, project_id=project_id)
            return project_user.role
        except DoesNotExist:
            return None

    @staticmethod
    async def get_project_admin(project_id: int) -> Optional[str]:
        """
        Gets the ID of the admin of a project.

        Args:
            project_id: project ID to filter by.

        Returns:
            User ID of the admin or None if there is no admin.
        """
        try:
            project_user = await ProjectUser.get(project_id=project_id, role=ProjectRole.ADMIN)
            return project_user.user.id
        except DoesNotExist:
            return None

    @staticmethod
    async def get_project_members(project_id: int) -> List[Dict[str, Any]]:
        """
        Gets all members of a project with their roles.

        Args:
            project_id: project ID

        Returns:
            List of dictionaries with members information and their roles.
        """
        project_users = await ProjectUser.filter(project_id=project_id).prefetch_related('user')

        members = []
        for pu in project_users:
            user_data = {
                'user_id': pu.user.id,
                'username': pu.user.username,
                'first_name': pu.user.first_name,
                'role': pu.role.value
            }
            members.append(user_data)

        return members

    @staticmethod
    @atomic()
    async def create_project(
            project_data: Union[Dict[str, Any], ProjectCreate_Pydantic],
            admin_user_id: int,
            member_ids: Optional[List[int]] = None
    ) -> Project_Pydantic:
        """
        Creates a new project with an admin and additional members (optional).

        Args:
            project_data: Project data to create
            admin_user_id: user ID of the admin
            member_ids: Optional list of user IDs to add as members (default: None)

        Returns:
            Created project

        Raises:
            DoesNotExist: If none of the users exist
            ValueError: If there are problems with the project data
        """
        # Turn Enums into strings if it's a dictionary
        if isinstance(project_data, Dict):
            # If status is an Enum, convert it into a string
            if 'status' in project_data and isinstance(project_data['status'], ProjectStatus):
                project_data['status'] = project_data['status'].value

            # Now we can use Pydantic to validate
            project_data = ProjectCreate_Pydantic(**project_data)


        # Verify that the admin exists
        admin_user = await User.get(id=admin_user_id)



        # Create the project
        project = await Project.create(
            name=project_data.name,
            description=project_data.description,
            telegram_chat_id=project_data.telegram_chat_id,
            status=project_data.status if hasattr(project_data, 'status') else ProjectStatus.ACTIVE.value
        )



        existing_admin = await ProjectUser.filter(project=project, role=ProjectRole.ADMIN).exists()
        if existing_admin:
            raise ValueError("This project has already an assigned admin.")

        # Assign the admin
        await ProjectUser.create(
            project=project,
            user=admin_user,
            role=ProjectRole.ADMIN
        )

        # Add members if provided
        if member_ids:
            for member_id in member_ids:
                # Check if member exists
                member = await User.get(id=member_id) # CHANGE TO INT ID to iterate

                # Don't add the admin as a regular member
                if member.id != admin_user_id:
                    await ProjectUser.create(
                        project=project,
                        user=member,
                        role=ProjectRole.MEMBER
                    )

        return await Project_Pydantic.from_tortoise_orm(project)

    @staticmethod
    @atomic()
    async def update_project(
            project_id: int,
            project_data: Dict[str, Any],
            user_id: int
    ) -> Optional[Project_Pydantic]:
        """
        Updates an existing project if the user has admin permissions.

        Args:
            project_id: project ID
            project_data: project data to update
            user_id: user ID to verify permissions (admin)

        Returns:
            Updated project or None if the user doesn't have permissions or the project doesn't exist.

        Raises:
            ValueError: If there are problems with the project data
        """
        try:
            # Verify that the user is the project's admin
            project_user = await ProjectUser.get(project_id=project_id, user_id=user_id)
            if project_user.role != ProjectRole.ADMIN:
                return None

            # Get and update the project
            project = await Project.get(id=project_id)

            # Only update the provided fields
            if 'name' in project_data:
                project.name = project_data['name']
            if 'description' in project_data:
                project.description = project_data['description']
            if 'status' in project_data:
                # Manage Enum objects and string values
                if isinstance(project_data['status'], ProjectStatus):
                    project.status = project_data['status'].value
                else:
                    project.status = project_data['status']
            if 'telegram_chat_id' in project_data:
                project.telegram_chat_id = project_data['telegram_chat_id']

            await project.save()
            return await Project_Pydantic.from_tortoise_orm(project)

        except DoesNotExist:
            return None

    @staticmethod
    @atomic()
    async def add_member_to_project(
            project_id: int,
            member_id: int,
            admin_id: int
    ) -> bool:
        """
        Add a member to a project, verifying that the requester is an admin.

        Args:
            project_id: project ID
            member_id: user ID to add as member
            admin_id: user ID of the requester

        Returns:
            True if added successfully, False otherwise
        """
        try:
            # Verify that the requester is the admin
            admin_role = await ProjectUser.get(project_id=project_id, user_id=admin_id, role=ProjectRole.ADMIN)

            # Verify if the project exists
            project = await Project.get(id=project_id)

            # Verify that member exists
            member = await User.get(id=member_id)

            # Verify that the member is not already in the project
            existing = await ProjectUser.filter(project_id=project_id, user_id=member_id).exists()
            if existing:
                return False

            # Add the member to the project
            await ProjectUser.create(
                project=project,
                user=member,
                role=ProjectRole.MEMBER
            )

            return True

        except DoesNotExist:
            return False

    @staticmethod
    @atomic()
    async def remove_member_from_project(
            project_id: int,
            member_id: int,
            admin_id: int
    ) -> bool:
        """
        Deletes a member from the project, verifying that the requester is an admin.

        Args:
            project_id: project ID
            member_id: meber ID to remove
            admin_id: ID of the admin user who authorizes the action

        Returns:
            True if removed successfully, False otherwise
        """
        try:
            # Verify that the requester is the admin
            admin_role = await ProjectUser.get(project_id=project_id, user_id=admin_id, role=ProjectRole.ADMIN)

            # Don't allow removing the admin from the project
            if member_id == admin_id:
                return False

            # Verify that the member exists in the project
            member_role = await ProjectUser.get(project_id=project_id, user_id=member_id)

            # Delete the member from the project
            await member_role.delete()

            return True

        except DoesNotExist:
            return False

    @staticmethod
    @atomic()
    async def change_project_admin(
            project_id: int,
            new_admin_id: int,
            current_admin_id: int
    ) -> bool:
        """
        Changes the admin of a project, verifying that the requester is the current admin.

        Args:
            project_id: project ID
            new_admin_id: new admin ID to assign
            current_admin_id: current admin ID

        Returns:
            True if the admin was changed successfully, False otherwise.
        """
        try:
            # Verify that the requester is the current admin
            current_admin = await ProjectUser.get(
                project_id=project_id,
                user_id=current_admin_id,
                role=ProjectRole.ADMIN
            )

            # Verify that the new admin exists and is already a member of the project
            new_admin_member = await ProjectUser.get(project_id=project_id, user_id=new_admin_id)

            # Change roles
            current_admin.role = ProjectRole.MEMBER
            await current_admin.save()

            new_admin_member.role = ProjectRole.ADMIN
            await new_admin_member.save()

            return True

        except DoesNotExist:
            return False

    @staticmethod
    @atomic()
    async def delete_project(project_id: int, admin_id: int) -> bool:
        """
        Deletes a project and all its relations, verifying that the requester is an admin.

        Args:
            project_id: project ID to delete
            admin_id: admin ID who authorized the action

        Returns:
            True if the project was deleted successfully, False otherwise.
        """
        """try:
            # Verify that the requester is the admin
            admin_role = await ProjectUser.get(
                project_id=project_id,
                user_id=admin_id,
                role=ProjectRole.ADMIN
            )

            if not admin_role:
                return False

            # Get the project
            project = await Project.get(id=project_id)

            # Deletes all user-project relations for the project
            await ProjectUser.filter(project_id=project_id).delete()

            # Delete all tasks for the project (if there are any)
            #await project.tasks.all().delete()

            # Delete the project
            await project.delete()

            return True

        except DoesNotExist:
            return False"""
        try:
            # Verify admin permissions
            admin_exists = await ProjectUser.exists(
                project_id=project_id,
                user_id=admin_id,
                role=ProjectRole.ADMIN
            )

            if not admin_exists:
                return False

            # Delete in secure order to avoid FK problems
            # 1. Delete all project tasks
            await Task.filter(project_id=project_id).delete()

            # 2. Delete all Project User relations
            await ProjectUser.filter(project_id=project_id).delete()

            # 3. Delete project
            await Project.filter(id=project_id).delete()

            return True

        except DoesNotExist:
            return False
