import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

class Settings:
    PROJECT_NAME: str = "Collabotus"
    PROJECT_VERSION: str = "0.1.0"

    BOT_USERNAME: str = os.getenv("BOT_USERNAME")

    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN")
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL")
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")

    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # LLM config
    GEMINI_KEY: str = os.getenv("GEMINI_API_KEY")
    LLM_MODEL: str = os.getenv("LLM_MODEL")

    # Additional config
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


# Config instance
settings = Settings()