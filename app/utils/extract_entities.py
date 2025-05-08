import re
from telegram import Update
from app.config import settings

async def extract_entities(update: Update, command: str):
    message = update.message

    if message.entities:
        print("ENTIDADES: ", message.entities)
        for entity in message.entities:
            if entity.type == "mention":
                mention_text = message.text[entity.offset:entity.offset + entity.length]
                if mention_text.lower() == f"@{settings.BOT_USERNAME}".lower():
                    # Extraer el texto después de la mención
                    remaining_text = message.text[entity.offset + entity.length:].strip()
                    # Buscar el comando (con o sin '/')
                    command_match = re.match(r'^/?(\w+)', remaining_text)
                    if command_match:
                        command = command_match.group(1).lower()
                    break
    return command