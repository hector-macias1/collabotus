import logging
from fastapi import FastAPI, Request, HTTPException
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, Application, MessageHandler, filters, CallbackQueryHandler

from app.bot.handlers.update_handler import actualizar_habilidades_command, handle_survey_response2
from app.config import settings
from app.models.db import init_db, close_db
from app.bot.handlers.base_handlers import start_command, ayuda_command, handle_message
from app.bot.handlers.register_handler import registro_command, handle_survey_response

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, settings.LOG_LEVEL)
)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

# Telegram app instance
telegram_application: Application = None


@app.get("/")
async def root():
    return {"message": "Collabotus API is running"}


@app.post(f"/webhook/{settings.WEBHOOK_SECRET}")
async def telegram_webhook(request: Request):
    if not settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Webhook secret not configured")

    data = await request.json()
    logger.debug(f"Received update: {data}")

    update = Update.de_json(data, telegram_application.bot)
    await telegram_application.update_queue.put(update)

    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    global telegram_application

    # Initialize DB
    await init_db()

    if settings.TELEGRAM_TOKEN and settings.WEBHOOK_URL and settings.WEBHOOK_SECRET:
        # Configure Telegram application
        telegram_application = (
            ApplicationBuilder()
            .token(settings.TELEGRAM_TOKEN)
            .build()
        )

        # Register handlers
        telegram_application.add_handler(CommandHandler("start", start_command))
        telegram_application.add_handler(CommandHandler("ayuda", ayuda_command))

        telegram_application.add_handler(CommandHandler("registro", registro_command))
        telegram_application.add_handler(CommandHandler("actualizar_habilidades", actualizar_habilidades_command))
        telegram_application.add_handler(CallbackQueryHandler(handle_survey_response))

        telegram_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Initialize app
        await telegram_application.initialize()

        # Initialize background processes
        await telegram_application.start()

        # Configure webhook
        webhook_url = f"{settings.WEBHOOK_URL}/webhook/{settings.WEBHOOK_SECRET}"
        await telegram_application.bot.set_webhook(webhook_url)
        logger.info(f"Webhook configured at: {webhook_url}")


@app.on_event("shutdown")
async def shutdown_event():
    global telegram_application

    # Stop Telegram application
    if telegram_application:
        await telegram_application.stop()
        await telegram_application.shutdown()

    # Close DB connection
    await close_db()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)