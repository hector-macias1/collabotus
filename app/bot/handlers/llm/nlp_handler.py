from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from app.bot.handlers.llm.intent_classifier import IntentClassifier
from app.bot.handlers.llm.intent_resolver import IntentResolver

class NLPHandler:
    def __init__(self, api_key: str, model: str):
        self.classifier = IntentClassifier(api_key, model)
        self.resolver = IntentResolver()

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Verify if it's a mention in a group or a private message
        #is_private = update.message.chat.type == "private"
        is_private = update.message.chat.type
        print("CHAT TYPE ", is_private)

        user_message = update.message.text

        is_mention = (
            not is_private
            and update.message.entities
            and any(entity.type == "mention" for entity in update.message.entities)
        )

        if not (is_private or is_mention):
            await update.message.reply_text("⚠️ Este comando solo está disponible en chats privados.")
            return  # Ignore messages in groups without mention

        # Extract text without mention (@bot)
        #user_message = update.message.text
        if is_mention:
            user_message = user_message.replace("@bot", "").strip()
            print("EXTRACTED MESSAGE: ", user_message)

        if is_private:
            if not user_message.startswith("?"):
                await update.message.reply_text(
                    "📝 Si quieres que procese tu mensaje con inteligencia artificial, comienza el mensaje con `?`.\n\n"
                    "Ejemplo: `? quiero actualizar mis habilidades`"
                )
                return
            user_message = user_message.lstrip("?").strip()

        # Classify and resolve intent
        intent = await self.classifier.classify(user_message)
        await self.resolver.resolve(intent, update, context)