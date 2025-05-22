from app.bot.handlers.base_handlers import ayuda_command
from app.bot.handlers.register_handler import registro_command
from app.bot.handlers.task_handler import agregar_tarea_nlp
from app.bot.handlers.update_handler import actualizar_habilidades_command
#from app.bot.handlers.project_handler import crear_proyecto_command, handle_nlp_project
from app.bot.handlers.project_handler2 import  crear_proyecto_command, handle_nlp_project
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from app.utils.extract_data import extract_project_data, extract_task_data


class IntentResolver:
    INTENT_HANDLERS = {
        "registro": registro_command,
        "actualizar_habilidades": actualizar_habilidades_command,
        "crear_proyecto_nlp": handle_nlp_project,
        "agregar_tarea_nlp": agregar_tarea_nlp,
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

        if intent == "agregar_tarea_nlp":
            params = await extract_task_data(text)
            context.user_data["task_data"] = params
            print("PARAMS: ", params)

        print("this command will be executed: ", handler.__name__)
        await handler(update, context)

        # Verify if command requires private chat
        """
        if getattr(handler, "_private_only", False) and not update.message.chat.type == "private":
            await update.message.reply_text("⚠️ Este comando solo está disponible en chats privados.")
            return
            
        """