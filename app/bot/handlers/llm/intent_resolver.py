from app.bot.handlers.base_handlers import ayuda_command
from app.bot.handlers.update_handler import actualizar_habilidades_command
from app.bot.handlers.project_handler import crear_proyecto_command, handle_nlp_project
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from app.utils.extract_data import extract_project_data

class IntentResolver:
    INTENT_HANDLERS = {
        "actualizar_habilidades": actualizar_habilidades_command,
        "crear_proyecto": crear_proyecto_command,
        "crear_proyecto_nlp": handle_nlp_project,
        "ayuda": ayuda_command,
    }

    async def resolve(self, intent: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        handler = self.INTENT_HANDLERS.get(intent)

        if not handler:
            return

        text = update.message.text
        print("USER MESSAGE: ", text)

        # Extract parameters based on the intent
        if intent == "crear_proyecto_nlp":
            params = await extract_project_data(text)
            context.user_data["project_data"] = params
            print("PARAMS: ", params)

        print("this command will be executed: ", handler.__name__)
        await handler(update, context)

        # Verify if command requires private chat
        """
        if getattr(handler, "_private_only", False) and not update.message.chat.type == "private":
            await update.message.reply_text("⚠️ Este comando solo está disponible en chats privados.")
            return
            
        """