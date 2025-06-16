import re
from telegram import Update
from app.config import settings

async def extract_command(update: Update, command: str):
    message = update.message

    if message.entities:
        print("ENTITIES: ", message.entities)
        for entity in message.entities:
            if entity.type == "mention":
                mention_text = message.text[entity.offset:entity.offset + entity.length]
                if mention_text.lower() == f"@{settings.BOT_USERNAME}".lower():
                    # Extract text after mention
                    remaining_text = message.text[entity.offset + entity.length:].strip()
                    print("\n\nMESSAGE: ", remaining_text)
                    return remaining_text
    return command