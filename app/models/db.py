from tortoise import Tortoise
from app.config import settings

TORTOISE_ORM = {
    "connections": {"default": settings.DATABASE_URL},
    "apps": {
        "models": {
            "models": ["app.db.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}

async def init_db():
    """
    Initialize connection to DB
    """
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.db.models"]}
    )
    # Genera el esquema
    await Tortoise.generate_schemas()

async def close_db():
    """
    Close connection to DB
    """
    await Tortoise.close_connections()