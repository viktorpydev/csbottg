from dataclasses import dataclass
from typing import Optional, List
import aiosqlite
from bot.database.db import get_db_connection


@dataclass
class User:
    id: int
    telegram_id: int
    full_name: Optional[str]
    username: Optional[str]
    opp_group: Optional[str]
    english_group: Optional[str]
    notify_minutes: int = 10
    notifications_enabled: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> "User":
        return cls(
            id=row["id"],
            telegram_id=row["telegram_id"],
            full_name=row["full_name"],
            username=row["username"],
            opp_group=row["opp_group"],
            english_group=row["english_group"],
            notify_minutes=row["notify_minutes"] if row["notify_minutes"] is not None else 10,
            notifications_enabled=bool(row["notifications_enabled"]),
            created_at=str(row["created_at"]) if "created_at" in row.keys() else None,
            updated_at=str(row["updated_at"]) if "updated_at" in row.keys() else None,
        )


async def get_or_create_user(telegram_id: int, full_name: Optional[str] = None, username: Optional[str] = None) -> User:
    """Отримання користувача з БД або створення нового запису."""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = await cursor.fetchone()
        if row:
            # Оновлення імені/юзернейму при зміні
            await conn.execute(
                "UPDATE users SET full_name = ?, username = ?, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
                (full_name, username, telegram_id)
            )
            await conn.commit()
            cursor = await conn.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            row = await cursor.fetchone()
            return User.from_row(row)
        else:
            await conn.execute(
                """
                INSERT INTO users (telegram_id, full_name, username, notify_minutes, notifications_enabled)
                VALUES (?, ?, ?, 10, 1)
                """,
                (telegram_id, full_name, username)
            )
            await conn.commit()
            cursor = await conn.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            row = await cursor.fetchone()
            return User.from_row(row)
    finally:
        await conn.close()


async def get_user(telegram_id: int) -> Optional[User]:
    """Отримання користувача за Telegram ID."""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = await cursor.fetchone()
        return User.from_row(row) if row else None
    finally:
        await conn.close()


async def update_user_opp_group(telegram_id: int, opp_group: str) -> None:
    """Оновлення основної групи ОПП користувача."""
    conn = await get_db_connection()
    try:
        await conn.execute(
            "UPDATE users SET opp_group = ?, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
            (opp_group, telegram_id)
        )
        await conn.commit()
    finally:
        await conn.close()


async def update_user_english_group(telegram_id: int, english_group: str) -> None:
    """Оновлення підгрупи з англійської мови користувача."""
    conn = await get_db_connection()
    try:
        await conn.execute(
            "UPDATE users SET english_group = ?, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
            (english_group, telegram_id)
        )
        await conn.commit()
    finally:
        await conn.close()


async def update_user_notification_settings(
    telegram_id: int,
    notify_minutes: Optional[int] = None,
    notifications_enabled: Optional[bool] = None
) -> None:
    """Оновлення налаштувань сповіщень користувача."""
    conn = await get_db_connection()
    try:
        updates = []
        params = []
        if notify_minutes is not None:
            updates.append("notify_minutes = ?")
            params.append(notify_minutes)
        if notifications_enabled is not None:
            updates.append("notifications_enabled = ?")
            params.append(1 if notifications_enabled else 0)

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(telegram_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE telegram_id = ?"
            await conn.execute(query, tuple(params))
            await conn.commit()
    finally:
        await conn.close()


async def get_all_active_users() -> List[User]:
    """Отримання всіх користувачів зі ввімкненими сповіщеннями та обраними групами."""
    conn = await get_db_connection()
    try:
        cursor = await conn.execute(
            """
            SELECT * FROM users
            WHERE notifications_enabled = 1
              AND opp_group IS NOT NULL
              AND english_group IS NOT NULL
            """
        )
        rows = await cursor.fetchall()
        return [User.from_row(row) for row in rows]
    finally:
        await conn.close()
