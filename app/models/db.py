from tortoise import Tortoise
from app.config import settings

TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.sqlite",
            "credentials": {
                "file_path": "db.sqlite3"  # Archivo SQLite
            }
        }
    },
    "apps": {
        "models": {
            "models": ["app.models.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}

async def init_db():
    """
    Initialize connection to DB
    """
    await Tortoise.init(config=TORTOISE_ORM)
    # Generate the schema
    await Tortoise.generate_schemas()

async def close_db():
    """
    Close connection to DB
    """
    await Tortoise.close_connections()