from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, CallbackQueryHandler, filters

from app.bot.handlers.update_task_handler import get_update_task_conversation_handler
from app.config import settings
from app.bot.handlers.base_handlers import start_command, ayuda_command, handle_message
from app.bot.handlers.project_handler import (
    crear_proyecto_command,
    handle_private_message,
    #misproyectos_command,
    #finalizarproyecto_command
)
from app.bot.handlers.project_handler2 import get_project_conversation_handler, misproyectos_command, finalizarproyecto_command, confirm_delete_handler
from app.bot.handlers.task_handler import agregar_tarea_command
from app.bot.handlers.premium_handler import premium_command
from app.bot.handlers.register_handler import registro_command, handle_survey_response
from app.bot.handlers.update_handler import actualizar_habilidades_command, handle_survey_response2
from app.bot.handlers.task_handler import get_task_conversation_handler, listar_tareas_command
from app.bot.handlers.llm.nlp_handler import NLPHandler


class BotManager:
    def __init__(self):
        self.application = None
        self.bot_username = settings.BOT_USERNAME
        self.nlp_handler = None

    async def initialize(self):
        """Initializes the Telegram application"""
        self.nlp_handler = NLPHandler(
            api_key=settings.GEMINI_KEY,
            model=settings.LLM_MODEL
        )

        self.application = (
            ApplicationBuilder()
            .token(settings.TELEGRAM_TOKEN)
            .build()
        )

        await self._register_handlers()
        await self.application.initialize()
        await self.application.start()

    async def _register_handlers(self):
        """Registers all the handlers"""

        # Basic handlers
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("ayuda", ayuda_command))

        # Project handlers
        #self.application.add_handler(CommandHandler("nuevoproyecto", crear_proyecto_command))
        self.application.add_handler(CommandHandler("misproyectos", misproyectos_command))
        self.application.add_handler(CommandHandler("finalizarproyecto", finalizarproyecto_command))
        self.application.add_handler(CallbackQueryHandler(confirm_delete_handler, pattern="confirm_delete*"))

        # Premium
        self.application.add_handler(CommandHandler("premium", premium_command))

        # Task handlers
        #self.application.add_handler(CommandHandler("agregartarea", agregar_tarea_command))
        self.application.add_handler(CommandHandler("listartareas", listar_tareas_command))
        self.application.add_handler(get_update_task_conversation_handler())

        # Register handlers
        self.application.add_handler(CommandHandler("registro", registro_command))
        self.application.add_handler(CommandHandler("actualizar_habilidades", actualizar_habilidades_command))
        self.application.add_handler(CallbackQueryHandler(handle_survey_response))
        #self.application.add_handler(CallbackQueryHandler(handle_survey_response2))

        # Conversation handlers
        self.application.add_handler(get_project_conversation_handler())
        self.application.add_handler(get_task_conversation_handler())


        # NLP handlers
        private_filter = filters.Regex(rf'^\?') & filters.ChatType.PRIVATE
        mention_filter = filters.Regex(rf"^@{self.bot_username}\b") & filters.ChatType.GROUPS

        self.application.add_handler(MessageHandler(private_filter, self.nlp_handler.handle_message))
        self.application.add_handler(MessageHandler(mention_filter, self.nlp_handler.handle_message))

        # Private messages handlers
        #self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_private_message))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_message))

    async def shutdown(self):
        """Shuts down the Telegram application"""
        if self.application:
            await self.application.stop()
            await self.application.shutdown()

    async def set_webhook(self):
        """Configures the webhook"""
        webhook_url = f"{settings.WEBHOOK_URL}/webhook/{settings.WEBHOOK_SECRET}"
        await self.application.bot.set_webhook(webhook_url)