import re
from telegram import Update
from app.config import settings

async def extract_command(update: Update, command: str):
    message = update.message

    if message.entities:
        print("ENTIDADES: ", message.entities)
        for entity in message.entities:
            if entity.type == "mention":
                mention_text = message.text[entity.offset:entity.offset + entity.length]
                if mention_text.lower() == f"@{settings.BOT_USERNAME}".lower():
                    # Extraer el texto después de la mención
                    remaining_text = message.text[entity.offset + entity.length:].strip()
                    print("\n\nMENSAJE: ", remaining_text)
                    return remaining_text
    return command