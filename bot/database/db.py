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
    has_management INTEGER DEFAULT 0,
    pe_slots TEXT DEFAULT NULL,
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

        for col, col_type in [
            ("prog_group", "TEXT"),
            ("math_group", "TEXT"),
            ("ukr_group", "TEXT"),
            ("has_management", "INTEGER DEFAULT 0"),
            ("pe_slots", "TEXT DEFAULT NULL"),
        ]:
            if col not in columns:
                await db.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
        await db.commit()

        # Міграція старих номерів груп англійської мови (A53-A67 -> A51-A65)
        eng_remap = {
            "A53": "A51",
            "A54": "A52",
            "A55": "A53",
            "A56": "A54",
            "A57": "A55",
            "A58": "A56",
            "A59": "A57",
            "A60": "A58",
            "A61": "A59",
            "A62": "A60",
            "A63": "A61",
            "A64": "A62",
            "A65": "A64",
            "A66": "A65",
            "A67": "A65",
        }
        for old_g, new_g in eng_remap.items():
            await db.execute(
                "UPDATE users SET english_group = ? WHERE english_group = ?",
                (new_g, old_g)
            )
        await db.commit()

    logger.info(f"Database initialized at {db_path}")


async def get_db_connection():
    """Отримання асинхронного підключення до бази даних."""
    conn = await aiosqlite.connect(config.DATABASE_PATH)
    conn.row_factory = aiosqlite.Row
    return conn
