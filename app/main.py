import logging
from fastapi import FastAPI, Request, HTTPException
from telegram import Update

from app.config import settings
from app.models.db import init_db, close_db
from app.bot.core import BotManager

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, settings.LOG_LEVEL)
)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)
bot_manager = BotManager()


@app.get("/")
async def root():
    return {"message": "Collabotus API is running"}


@app.post(f"/webhook/{settings.WEBHOOK_SECRET}")
async def telegram_webhook(request: Request):
    if not settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Webhook secret not configured")

    data = await request.json()
    logger.debug(f"Received update: {data}")

    update = Update.de_json(data, bot_manager.application.bot)
    await bot_manager.application.update_queue.put(update)

    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    await init_db()

    if settings.TELEGRAM_TOKEN and settings.WEBHOOK_URL and settings.WEBHOOK_SECRET:
        await bot_manager.initialize()
        await bot_manager.set_webhook()
        logger.info(f"Webhook configured")


@app.on_event("shutdown")
async def shutdown_event():
    await bot_manager.shutdown()
    await close_db()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)