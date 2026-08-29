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
    english_group TEXT,
    notify_minutes INTEGER DEFAULT 10,
    notifications_enabled INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


async def init_db():
    """Ініціалізація бази даних SQLite та її таблиць."""
    db_path = config.DATABASE_PATH
    async with aiosqlite.connect(db_path) as db:
        await db.execute(CREATE_USERS_TABLE)
        await db.commit()
    logger.info(f"Database initialized at {db_path}")


async def get_db_connection():
    """Отримання асинхронного підключення до бази даних."""
    conn = await aiosqlite.connect(config.DATABASE_PATH)
    conn.row_factory = aiosqlite.Row
    return conn
