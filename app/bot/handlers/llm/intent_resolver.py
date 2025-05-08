from app.bot.handlers.update_handler import actualizar_habilidades_command
from app.bot.handlers.project_handler import crear_proyecto_command
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

class IntentResolver:
    INTENT_HANDLERS = {
        "actualizar_habilidades": actualizar_habilidades_command,
        "crear_proyecto": crear_proyecto_command,
    }

    async def resolve(self, intent: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        handler = self.INTENT_HANDLERS.get(intent)
        if not handler:
            return

        # Verify if command requires private chat
        if getattr(handler, "_private_only", False) and not update.message.chat.type == "private":
            await update.message.reply_text("⚠️ Este comando solo está disponible en chats privados.")
            return

        await handler(update, context)