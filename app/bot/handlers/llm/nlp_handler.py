import re
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from app.bot.handlers.llm.intent_classifier import IntentClassifier
from app.bot.handlers.llm.intent_resolver import IntentResolver
from app.utils.extract_command import extract_command

BOT_USERNAME = "CollabotusBot"

class NLPHandler:
    def __init__(self, api_key: str, model:str):
        self.classifier = IntentClassifier(api_key, model)
        self.resolver = IntentResolver()

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text

        chat_type = update.message.chat.type
        command = None

        # En grupo o supergrupo: buscar mención y comando
        if chat_type in ["group", "supergroup"]:
            clean_message = await extract_command(update, command)
            # Clasificar y resolver intención
            intent = await self.classifier.classify(clean_message)
            await self.resolver.resolve(intent, update, context)
            return

            # En chats privados: extraer directamente
        if chat_type == "private":
            clean_message = user_message.strip()

        if not user_message.startswith("?"):
            await update.message.reply_text(
                "📝 Si quieres que procese tu mensaje con inteligencia artificial, comienza el mensaje con `?`.\n\n"
                "Ejemplo: `? quiero actualizar mis habilidades`"
            )
            return

        # Clasificar y resolver intención
        intent = await self.classifier.classify(clean_message)
        await self.resolver.resolve(intent, update, context)
