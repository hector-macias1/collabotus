from telegram import Update, Chat
from telegram.constants import ChatType
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

# Almacena el progreso del usuario
user_project_creation = {}

async def crear_proyecto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user_id = update.effective_user.id

    if chat.type != ChatType.GROUP and chat.type != ChatType.SUPERGROUP:
        await update.message.reply_text("❗ Este comando solo puede usarse desde un chat grupal.")
        return

    # Guardamos el ID del grupo para usarlo luego
    user_project_creation[user_id] = {
        "group_id": chat.id,
        "step": "ask_name"
    }

    # Enviar mensaje privado al usuario
    await context.bot.send_message(
        chat_id=user_id,
        text="📝 ¡Hola! Vamos a crear un nuevo proyecto.\n\nPor favor, envíame el *nombre del proyecto*:",
        parse_mode="Markdown"
    )

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text

    if user_id not in user_project_creation:
        await update.message.reply_text("❗ Introduce un comando válido")
        return

    user_data = user_project_creation[user_id]

    if user_data["step"] == "ask_name":
        user_data["project_name"] = message
        user_data["step"] = "ask_description"
        await update.message.reply_text("📄 Genial. Ahora envíame la *descripción del proyecto*:", parse_mode="Markdown")

    elif user_data["step"] == "ask_description":
        user_data["description"] = message

        # Mostrar resumen
        name = user_data["project_name"]
        desc = user_data["description"]
        resumen = f"✅ Proyecto creado:\n\n*Nombre:* {name}\n*Descripción:* {desc}"
        await update.message.reply_text(resumen, parse_mode="Markdown")

        # Opcional: enviar al grupo
        group_id = user_data["group_id"]
        await context.bot.send_message(
            chat_id=group_id,
            text=f"🚀 Se ha creado un nuevo proyecto por @{update.effective_user.username}:\n\n*{name}*\n_{desc}_",
            parse_mode="Markdown"
        )

        # Limpiar estado
        del user_project_creation[user_id]