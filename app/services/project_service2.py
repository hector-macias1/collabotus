from typing import List, Optional, Union, Dict, Any, Tuple
from tortoise.exceptions import DoesNotExist
from tortoise.transactions import atomic

from app.models.models import (
    Project, User, ProjectUser, ProjectRole, ProjectStatus,
    Project_Pydantic, ProjectCreate_Pydantic,
    ProjectUser_Pydantic, ProjectUserCreate_Pydantic
)


class ProjectService:
    """
    Servicio para gestionar operaciones relacionadas con proyectos.
    """

    @staticmethod
    async def get_project_by_id(project_id: int) -> Optional[Project_Pydantic]:
        """
        Obtiene un proyecto por su ID.

        Args:
            project_id: ID del proyecto

        Returns:
            Detalles del proyecto o None si no existe
        """
        try:
            project = await Project.get(id=project_id)
            return await Project_Pydantic.from_tortoise_orm(project)
        except DoesNotExist:
            return None

    @staticmethod
    async def get_projects_by_user(user_id: str) -> List[Project_Pydantic]:
        """
        Obtiene todos los proyectos en los que participa un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de proyectos
        """
        user = await User.get(id=user_id)
        projects = await user.projects
        print(projects)
        return [await Project_Pydantic.from_tortoise_orm(project) for project in projects]

    @staticmethod
    async def get_projects_by_status(status: Union[ProjectStatus, str]) -> List[Project_Pydantic]:
        """
        Obtiene todos los proyectos con un estado específico.

        Args:
            status: Estado del proyecto (puede ser un enum ProjectStatus o un string)

        Returns:
            Lista de proyectos con el estado especificado
        """
        # Manejar tanto objetos Enum como valores de string
        status_value = status.value if isinstance(status, ProjectStatus) else status
        projects = await Project.filter(status=status_value)
        return [await Project_Pydantic.from_tortoise_orm(project) for project in projects]

    @staticmethod
    async def get_user_role_in_project(user_id: str, project_id: int) -> Optional[ProjectRole]:
        """
        Obtiene el rol de un usuario en un proyecto específico.

        Args:
            user_id: ID del usuario
            project_id: ID del proyecto

        Returns:
            Rol del usuario en el proyecto o None si no pertenece al proyecto
        """
        try:
            project_user = await ProjectUser.get(user_id=user_id, project_id=project_id)
            return project_user.role
        except DoesNotExist:
            return None

    @staticmethod
    async def get_project_admin(project_id: int) -> Optional[str]:
        """
        Obtiene el ID del administrador de un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            ID del usuario administrador o None si no hay administrador
        """
        try:
            project_user = await ProjectUser.get(project_id=project_id, role=ProjectRole.ADMIN)
            return project_user.user_id
        except DoesNotExist:
            return None

    @staticmethod
    async def get_project_members(project_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todos los miembros de un proyecto con sus roles.

        Args:
            project_id: ID del proyecto

        Returns:
            Lista de diccionarios con información de los miembros y sus roles
        """
        project_users = await ProjectUser.filter(project_id=project_id).prefetch_related('user')

        members = []
        for pu in project_users:
            user_data = {
                'user_id': pu.user.id,
                'telegram_usr': pu.user.telegram_usr,
                'first_name': pu.user.first_name,
                'role': pu.role.value
            }
            members.append(user_data)

        return members

    @staticmethod
    @atomic()
    async def create_project(
            project_data: Union[Dict[str, Any], ProjectCreate_Pydantic],
            admin_user_id: str,
            member_ids: Optional[List[str]] = None
    ) -> Project_Pydantic:
        """
        Crea un nuevo proyecto con un administrador y opcionalmente miembros adicionales.

        Args:
            project_data: Datos del proyecto a crear
            admin_user_id: ID del usuario que será administrador
            member_ids: Lista opcional de IDs de usuarios que serán miembros

        Returns:
            Proyecto creado

        Raises:
            DoesNotExist: Si alguno de los usuarios no existe
            ValueError: Si hay problemas con los datos del proyecto
        """
        # Convertir Enums a valores string si es un diccionario
        if isinstance(project_data, Dict):
            # Si status es un Enum, convertirlo a string
            if 'status' in project_data and isinstance(project_data['status'], ProjectStatus):
                project_data['status'] = project_data['status'].value

            # Ahora podemos usar Pydantic para validar
            project_data = ProjectCreate_Pydantic(**project_data)

        # Verificar que el admin existe
        admin_user = await User.get(id=admin_user_id)



        # Crear el proyecto
        project = await Project.create(
            name=project_data.name,
            description=project_data.description,
            telegram_chat_id=project_data.telegram_chat_id,
            status=project_data.status if hasattr(project_data, 'status') else ProjectStatus.ACTIVE.value
        )



        existing_admin = await ProjectUser.filter(project=project, role=ProjectRole.ADMIN).exists()
        if existing_admin:
            raise ValueError("Este proyecto ya tiene un administrador asignado.")

        print(f"existing admin: {existing_admin}")

        # Asignar el administrador
        await ProjectUser.create(
            project=project,
            user=admin_user,
            role=ProjectRole.ADMIN
        )

        # Agregar miembros si existen
        if member_ids:
            for member_id in member_ids:
                # Verificar que el miembro existe
                member = await User.get(id=member_id)

                # No agregar al admin como miembro regular
                if member.id != admin_user_id:
                    await ProjectUser.create(
                        project=project,
                        user=member,
                        role=ProjectRole.MEMBER
                    )
                    print("Se creo un miembro")

        return await Project_Pydantic.from_tortoise_orm(project)

    @staticmethod
    @atomic()
    async def update_project(
            project_id: int,
            project_data: Dict[str, Any],
            user_id: str
    ) -> Optional[Project_Pydantic]:
        """
        Actualiza un proyecto existente verificando que el usuario tenga permisos de administrador.

        Args:
            project_id: ID del proyecto a actualizar
            project_data: Datos actualizados del proyecto
            user_id: ID del usuario que intenta actualizar el proyecto

        Returns:
            Proyecto actualizado o None si el usuario no tiene permisos o el proyecto no existe

        Raises:
            ValueError: Si hay problemas con los datos del proyecto
        """
        try:
            # Verificar que el usuario es administrador del proyecto
            project_user = await ProjectUser.get(project_id=project_id, user_id=user_id)
            if project_user.role != ProjectRole.ADMIN:
                return None

            # Obtener y actualizar el proyecto
            project = await Project.get(id=project_id)

            # Actualizar solo los campos proporcionados
            if 'name' in project_data:
                project.name = project_data['name']
            if 'description' in project_data:
                project.description = project_data['description']
            if 'status' in project_data:
                # Manejar tanto objetos Enum como valores de string
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
            member_id: str,
            admin_id: str
    ) -> bool:
        """
        Agrega un miembro a un proyecto, verificando que quien lo agrega es administrador.

        Args:
            project_id: ID del proyecto
            member_id: ID del usuario a agregar como miembro
            admin_id: ID del usuario administrador que autoriza la acción

        Returns:
            True si se agregó con éxito, False en caso contrario
        """
        try:
            # Verificar que el solicitante es administrador
            admin_role = await ProjectUser.get(project_id=project_id, user_id=admin_id, role=ProjectRole.ADMIN)

            # Verificar que el proyecto existe
            project = await Project.get(id=project_id)

            # Verificar que el miembro existe
            member = await User.get(id=member_id)

            # Verificar que el miembro no está ya en el proyecto
            existing = await ProjectUser.filter(project_id=project_id, user_id=member_id).exists()
            if existing:
                return False

            # Agregar al miembro
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
            member_id: str,
            admin_id: str
    ) -> bool:
        """
        Elimina un miembro de un proyecto, verificando que quien lo elimina es administrador.

        Args:
            project_id: ID del proyecto
            member_id: ID del usuario a eliminar
            admin_id: ID del usuario administrador que autoriza la acción

        Returns:
            True si se eliminó con éxito, False en caso contrario
        """
        try:
            # Verificar que el solicitante es administrador
            admin_role = await ProjectUser.get(project_id=project_id, user_id=admin_id, role=ProjectRole.ADMIN)

            # No permitir eliminar al administrador a sí mismo
            if member_id == admin_id:
                return False

            # Verificar que el miembro existe en el proyecto
            member_role = await ProjectUser.get(project_id=project_id, user_id=member_id)

            # Eliminar al miembro
            await member_role.delete()

            return True

        except DoesNotExist:
            return False

    @staticmethod
    @atomic()
    async def change_project_admin(
            project_id: int,
            new_admin_id: str,
            current_admin_id: str
    ) -> bool:
        """
        Cambia el administrador de un proyecto, verificando que quien lo solicita es el admin actual.

        Args:
            project_id: ID del proyecto
            new_admin_id: ID del usuario que será el nuevo administrador
            current_admin_id: ID del usuario administrador actual

        Returns:
            True si se cambió con éxito, False en caso contrario
        """
        try:
            # Verificar que el solicitante es el administrador actual
            current_admin = await ProjectUser.get(
                project_id=project_id,
                user_id=current_admin_id,
                role=ProjectRole.ADMIN
            )

            # Verificar que el nuevo admin existe y ya es miembro del proyecto
            new_admin_member = await ProjectUser.get(project_id=project_id, user_id=new_admin_id)

            # Cambiar roles
            current_admin.role = ProjectRole.MEMBER
            await current_admin.save()

            new_admin_member.role = ProjectRole.ADMIN
            await new_admin_member.save()

            return True

        except DoesNotExist:
            return False

    @staticmethod
    @atomic()
    async def delete_project(project_id: int, admin_id: str) -> bool:
        """
        Elimina un proyecto y todas sus relaciones, verificando que quien lo solicita es admin.

        Args:
            project_id: ID del proyecto a eliminar
            admin_id: ID del usuario administrador que autoriza la acción

        Returns:
            True si se eliminó con éxito, False en caso contrario
        """
        try:
            # Verificar que el solicitante es administrador
            admin_role = await ProjectUser.get(
                project_id=project_id,
                user_id=admin_id,
                role=ProjectRole.ADMIN
            )

            # Obtener el proyecto
            project = await Project.get(id=project_id)

            # Eliminar todas las relaciones de usuarios con el proyecto
            await ProjectUser.filter(project_id=project_id).delete()

            # Eliminar todas las tareas del proyecto (si las hay)
            await project.tasks.all().delete()

            # Eliminar el proyecto
            await project.delete()

            return True

        except DoesNotExist:
            return False
