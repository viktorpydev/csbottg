import aiosqlite
import logging
from bot.config import config

logger = logging.getLogger(__name__)

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    full_name TEXT,
    username TEXT,
    opp_group TEXT,
    prog_group TEXT,
    math_group TEXT,
    ukr_group TEXT,
    english_group TEXT,
    notify_minutes INTEGER DEFAULT 10,
    notifications_enabled INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


async def init_db():
    """Ініціалізація бази даних SQLite та її таблиць з автоматичною міграцією колонок."""
    db_path = config.DATABASE_PATH
    async with aiosqlite.connect(db_path) as db:
        await db.execute(CREATE_USERS_TABLE)
        await db.commit()

        # Автоматична міграція нових колонок, якщо БД вже існувала
        async with db.execute("PRAGMA table_info(users)") as cursor:
            columns = [row[1] for row in await cursor.fetchall()]

        for col in ["prog_group", "math_group", "ukr_group"]:
            if col not in columns:
                await db.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        await db.commit()
    logger.info(f"Database initialized at {db_path}")


async def get_db_connection():
    """Отримання асинхронного підключення до бази даних."""
    conn = await aiosqlite.connect(config.DATABASE_PATH)
    conn.row_factory = aiosqlite.Row
    return conn
