from telegram import Update, Chat
from telegram.constants import ChatType
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler
)
from app.models.models import ProjectStatus, ProjectCreate_Pydantic, ProjectUser
from app.models.models import User
from app.services.project_service import ProjectService

# Definición de estados para la conversación
ASK_NAME, ASK_DESC = range(2)


async def crear_proyecto_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        await update.message.reply_text("❗ Este comando solo puede usarse desde un chat grupal.")
        return ConversationHandler.END

    # Store temp data
    context.user_data['group_id'] = chat.id

    # Verify if user exists in DB
    if not (_user := await User.get_or_none(id=user.id)):
        await context.bot.send_message(
            chat_id=user.id,
            text="❗No estás registrado en el sistema. Utiliza el comando /registro para registrarte.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    # Verify if user has premium account to create more than one project

    # Send private message
    await context.bot.send_message(
        chat_id=user.id,
        text="📝 ¡Hola! Vamos a crear un nuevo proyecto.\n\nPor favor, envíame el *nombre del proyecto*:",
        parse_mode="Markdown"
    )
    return ASK_NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['project_name'] = update.message.text
    await update.message.reply_text(
        "📄 Genial. Ahora envíame la *descripción del proyecto*:",
        parse_mode="Markdown"
    )
    return ASK_DESC


async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    context.user_data['description'] = update.message.text
    print("entramos aqui")
    # Create project
    project_data = {
        "name": context.user_data['project_name'],
        "description": context.user_data['description'],
        "telegram_chat_id": str(context.user_data['group_id'])
    }

    new_project = await ProjectService.create_project(
        project_data=project_data,
        admin_user_id=user.id,
        member_ids=[]
    )

    # Notify group
    await context.bot.send_message(
        chat_id=context.user_data['group_id'],
        text=f"🚀 Se ha creado un nuevo proyecto por @{user.username}:\n\n"
             f"*{context.user_data['project_name']}*\n"
             f"_{context.user_data['description']}_",
        parse_mode="Markdown"
    )

    # Clean temp data
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("❌ Creación de proyecto cancelada.")
    return ConversationHandler.END


# Conversation handler
def get_project_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler('nuevoproyecto', crear_proyecto_command)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, get_name)],
            ASK_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, get_description)]
        },
        fallbacks=[CommandHandler('cancelar', cancel)],
        per_user=True,
        per_chat=False  # Allow cross conversation between chats
    )

async def misproyectos_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user_id = update.effective_user.id

    if chat.type != ChatType.PRIVATE:
        await update.message.reply_text("❗ Este comando sólo puede usarse desde un chat privado.")
        return

    projects = await ProjectService.get_projects_by_user(update.effective_user.id)

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
        await update.message.reply_text(
            f"No tienes ningún proyecto en este chat.\nPuedes crear uno usando el comando /crear_proyecto."
        )
        return

    try:
        await ProjectService.delete_project(project.id, user_id)
        await update.message.reply_text(f"Proyecto {project.name} eliminado exitosamente.")
    except Exception as e:
        await update.message.reply_text(f"Error al eliminar el proyecto: {e}")

async def handle_nlp_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text
    chat_id = update.effective_chat.id

    if update.effective_chat.type != ChatType.GROUP and update.effective_chat.type != ChatType.SUPERGROUP:
        await update.message.reply_text("❗ Este comando solo puede usarse desde un chat grupal.")
        return

    # Verify if user exists in DB
    if not (user := await User.get_or_none(id=user_id)):
        await update.message.reply_text(
            "❗No estás registrado en el sistema. Utiliza el comando /registro por chat privado para registrarte."
        )
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