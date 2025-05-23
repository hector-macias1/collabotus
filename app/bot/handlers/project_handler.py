from telegram import Update, Chat
from telegram.constants import ChatType
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from app.models.models import ProjectStatus, ProjectCreate_Pydantic, ProjectUser
from app.models.models import User
from app.services.project_service import ProjectService

# Save the user's progress in a dictionary:
user_project_creation = {}

async def crear_proyecto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user_id = update.effective_user.id

    if chat.type != ChatType.GROUP and chat.type != ChatType.SUPERGROUP:
        await update.message.reply_text("❗ Este comando solo puede usarse desde un chat grupal.")
        return

    # Save the chat ID in a dictionary for later use
    user_project_creation[user_id] = {
        "group_id": chat.id,
        "step": "ask_name"
    }

    # Verify if user exists in DB
    if not (user := await User.get_or_none(id=user_id)):
        await update.message.send_message(
            chat_id=user_id,
            text="❗No estás registrado en el sistema. Utiliza el comando /registro para registrarte.",
            parse_mode="Markdown"
        )
        return

    # Send private message to the user
    await context.bot.send_message(
        chat_id=user_id,
        text="📝 ¡Hola! Vamos a crear un nuevo proyecto.\n\nPor favor, envíame el *nombre del proyecto*:",
        parse_mode="Markdown"
    )

"""async def misproyectos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user_id = update.effective_user.id

    if chat.type != ChatType.PRIVATE:
        await update.message.reply_text("❗ Este comando sólo puede usarse desde un chat privado.")
        return

    projects = await ProjectService.get_projects_by_user(update.effective_user.id)

    print("PROYECTOS: ", projects)

    if not projects:
        await update.message.reply_text(
            "❗ No tienes ningun proyecto.\nPuedes crear uno usando el comando /nuevoproyecto en un chat grupal."
        )
        return

    await context.bot.send_message(
        chat_id=user_id,
        text=f"Estos son tus proyectos:\n",
        parse_mode="Markdown"
    )

    for project in projects:
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"{project.name}\n",
        )

async def finalizarproyecto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user_id = update.effective_user.id

    if chat.type != ChatType.GROUP and chat.type != ChatType.SUPERGROUP:
        await update.message.reply_text("❗ Sólo puedes eliminar un proyecto desde un chat grupal.")
        return

    project = await ProjectService.get_project_by_chat_id(str(chat.id))
    if not project:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"No tienes ningun proyecto en este chat.\nPuedes crear uno usando el comando /crear_proyecto.",
            parse_mode="Markdown"
        )
        return

    try:
        await ProjectService.delete_project(project.id, user_id)
        await update.message.reply_text(f"Proyecto {project.name} eliminado exitosamente.")
    except Exception as e:
        await update.message.reply_text(f"Error al eliminar el proyecto: {e}")
"""


async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text

    if user_id not in user_project_creation:
        await update.message.reply_text("❗ Introduce un comando válido")
        return

    user_data = user_project_creation[user_id]

    # 1. Ask for the project name
    if user_data["step"] == "ask_name":
        user_data["project_name"] = message
        user_data["step"] = "ask_description"
        await update.message.reply_text("📄 Genial. Ahora envíame la *descripción del proyecto*:", parse_mode="Markdown")

    elif user_data["step"] == "ask_description":
        user_data["description"] = message

        # Show summary
        name = user_data["project_name"]
        desc = user_data["description"]
        resumen = f"✅ Proyecto creado:\n\n*Nombre:* {name}\n*Descripción:* {desc}"
        await update.message.reply_text(resumen, parse_mode="Markdown")

        # Optional: Send to group
        group_id = user_data["group_id"]
        await context.bot.send_message(
            chat_id=group_id,
            text=f"🚀 Se ha creado un nuevo proyecto por @{update.effective_user.username}:\n\n*{name}*\n_{desc}_",
            parse_mode="Markdown"
        )

        # Create a dictionary with the data
        project_data = {
            "name": name,
            "description": desc,
            "telegram_chat_id": str(group_id)
        }

        new_project = await ProjectService.create_project(
            project_data=project_data,
            admin_user_id=update.effective_user.id,
            member_ids=[]
        )

        # Clean state
        del user_project_creation[user_id]

async def handle_nlp_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text
    chat_id = update.effective_chat.id

    if update.effective_chat.type != ChatType.GROUP and update.effective_chat.type != ChatType.SUPERGROUP:
        await update.message.reply_text("❗ Este comando solo puede usarse desde un chat grupal.")
        return

    data = context.user_data.get("project_data", {})

    name = data.get("nombre")
    description = data.get("descripcion")

    print(name, description)

    """if name or description is None:
        await update.message.reply_text("❗ Para crear un proyecto necesito que me des un nombre y su descripción.")
        return"""

    project_data = {
        "name": name,
        "description": description,
        "telegram_chat_id": str(chat_id)
    }

    new_project = await ProjectService.create_project(
        project_data=project_data,
        admin_user_id=update.effective_user.id,
        member_ids=[]
    )

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🚀 Se ha creado un nuevo proyecto por @{update.effective_user.username}:\n\n*{name}*\n_{description}_",
        parse_mode="Markdown"
    )