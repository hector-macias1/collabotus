import asyncio
from tortoise import Tortoise
from app.models.db import init_db
from app.models.models import User, Project, ProjectUser, ProjectRole, ProjectStatus
from app.services.project_service import ProjectService


async def test_project_service():
    print("Initializing ProjectService testing...")

    # Create sample users
    admin_user, created = await User.get_or_create(
        id=100000001,
        username="admin_telegram",
        first_name="Admin User"
    )

    member1, created = await User.get_or_create(
        id=100000002,
        username="member1",
        first_name="Member One"
    )

    member2, created = await User.get_or_create(
        id=100000003,
        username="member2",
        first_name="Member Two"
    )

    # 1. Create a new project with admin and members
    print("\n1. Creating new project...")
    project_data = {
        "name": "Proyecto Demo",
        "description": "This is a demo project",
        "telegram_chat_id": "12345",
        "status": ProjectStatus.ACTIVE.value  # We use .value to get the enum string
    }

    new_project = await ProjectService.create_project(
        project_data=project_data,
        admin_user_id=admin_user.id,
        member_ids=[member1.id, member2.id]
    )

    print(f"Proyecto creado: {new_project.name} (ID: {new_project.id})")

    # 2. Get project data
    print("\n2. Getting project data...")
    project = await ProjectService.get_project_by_id(new_project.id)
    print(f"Proyecto: {project.name}")

    # 2.1 Get projects by state
    print("\n2.1 Getting projects by their state...")
    # We can use both the enum and the string
    active_projects1 = await ProjectService.get_projects_by_status(ProjectStatus.ACTIVE)
    active_projects2 = await ProjectService.get_projects_by_status(ProjectStatus.ACTIVE.value)
    print(f"Proyectos activos encontrados (usando enum): {len(active_projects1)}")
    print(f"Proyectos activos encontrados (usando string): {len(active_projects2)}")

    # 3. Get project members
    print("\n3. Getting project members...")
    members = await ProjectService.get_project_members(new_project.id)
    for member in members:
        print(f"- {member['first_name']} ({member['role']})")

    # 4. Check a user's role in the project
    print("\n4. Verifying user's role...")
    admin_role = await ProjectService.get_user_role_in_project(admin_user.id, new_project.id)
    print(admin_role)
    print(f"{admin_user.first_name}'s role: {admin_role.value}")

    member_role = await ProjectService.get_user_role_in_project(member1.id, new_project.id)
    print(f"{member1.first_name}'s role: {member_role.value}")

    # 5. Update project data
    print("\n5. Updating project data...")
    updated_data = {
        "name": "Updated demo project",
        "description": "Updated description"
    }

    updated_project = await ProjectService.update_project(
        project_id=new_project.id,
        project_data=updated_data,
        user_id=admin_user.id
    )

    print(f"Updated project: {updated_project.name}")
    print(f"New description: {updated_project.description}")

    # 5.1 Update state using Enum object directly
    print("\n5.1 Updating state using Enum object directly...")
    updated_data_with_enum = {
        "status": ProjectStatus.TERMINATED  # Directly using the enum object
    }

    updated_project = await ProjectService.update_project(
        project_id=new_project.id,
        project_data=updated_data_with_enum,
        user_id=admin_user.id
    )

    print(f"Project's state updated to: {updated_project.status}")

    # 6. Add new member
    print("\n6. Creating new user and adding it to the project...")
    new_member = await User.create(
        id=100000004,
        username="new_member",
        first_name="New Member"
    )

    success = await ProjectService.add_member_to_project(
        project_id=new_project.id,
        member_id=new_member.id,
        admin_id=admin_user.id
    )

    if success:
        print(f"User {new_member.first_name} successfully added")

        # Verify updated members
        updated_members = await ProjectService.get_project_members(new_project.id)
        print("Updated members:")
        for member in updated_members:
            print(f"- {member['first_name']} ({member['role']})")

    # 7. Changing project administrator
    print("\n7. Changing project administrator...")
    changed = await ProjectService.change_project_admin(
        project_id=new_project.id,
        new_admin_id=member1.id,
        current_admin_id=admin_user.id
    )

    if changed:
        print(f"Administrator changed to {member1.first_name}")

        # Verify updated roles
        updated_members = await ProjectService.get_project_members(new_project.id)
        print("Updated roles:")
        for member in updated_members:
            print(f"- {member['first_name']} ({member['role']})")

    # 8. Get projects from a user
    print("\n8. Getting projects from a user...")
    user_projects = await ProjectService.get_projects_by_user(member1.id)
    print(f"Projects where {member1.first_name} participates:")
    for proj in user_projects:
        print(f"- {proj.name} (ID: {proj.id})")

    # 9. Remove a project member
    print("\n9. Removing a project member...")
    removed = await ProjectService.remove_member_from_project(
        project_id=new_project.id,
        member_id=member2.id,
        admin_id=member1.id  # now member1 is admin
    )

    if removed:
        print(f"User {member2.first_name} has been removed from project")

        # Verify updated members
        final_members = await ProjectService.get_project_members(new_project.id)
        print("Final members:")
        for member in final_members:
            print(f"- {member['first_name']} ({member['role']})")

    print("\nTest completed with success.")


async def main():
    await init_db()
    await test_project_service()
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())