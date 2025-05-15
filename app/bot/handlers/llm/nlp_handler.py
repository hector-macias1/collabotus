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

        clean_message = None

        # In group or supergroup: find mention and command
        if chat_type in ["group", "supergroup"]:
            clean_message = await extract_command(update, command)
            # Classify and resolve intent
            intent = await self.classifier.classify(clean_message)
            await self.resolver.resolve(intent, update, context)
            return

        # Extract directly if in private chat
        if chat_type == "private":
            clean_message = user_message.strip()

        if not user_message.startswith("?"):
            await update.message.reply_text(
                "📝 Si quieres que procese tu mensaje con inteligencia artificial, comienza el mensaje con `?`.\n\n"
                "Ejemplo: `? quiero actualizar mis habilidades`"
            )
            return

        # Classify and solve intent
        intent = await self.classifier.classify(clean_message)
        print("INTENT: ", intent)
        await self.resolver.resolve(intent, update, context)
