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
    prog_group: Optional[str] = None
    math_group: Optional[str] = None
    ukr_group: Optional[str] = None
    english_group: Optional[str] = None
    opp_group: Optional[str] = None
    notify_minutes: int = 10
    notifications_enabled: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> "User":
        keys = row.keys()
        return cls(
            id=row["id"],
            telegram_id=row["telegram_id"],
            full_name=row["full_name"],
            username=row["username"],
            prog_group=row["prog_group"] if "prog_group" in keys else None,
            math_group=row["math_group"] if "math_group" in keys else None,
            ukr_group=row["ukr_group"] if "ukr_group" in keys else None,
            english_group=row["english_group"] if "english_group" in keys else None,
            opp_group=row["opp_group"] if "opp_group" in keys else None,
            notify_minutes=row["notify_minutes"] if row["notify_minutes"] is not None else 10,
            notifications_enabled=bool(row["notifications_enabled"]),
            created_at=str(row["created_at"]) if "created_at" in keys else None,
            updated_at=str(row["updated_at"]) if "updated_at" in keys else None,
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


async def update_user_prog_group(telegram_id: int, prog_group: str) -> None:
    """Оновлення підгрупи з мов програмування (1-6)."""
    conn = await get_db_connection()
    try:
        await conn.execute(
            "UPDATE users SET prog_group = ?, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
            (prog_group, telegram_id)
        )
        await conn.commit()
    finally:
        await conn.close()


async def update_user_math_group(telegram_id: int, math_group: str) -> None:
    """Оновлення підгрупи з математики (1-3)."""
    conn = await get_db_connection()
    try:
        await conn.execute(
            "UPDATE users SET math_group = ?, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
            (math_group, telegram_id)
        )
        await conn.commit()
    finally:
        await conn.close()


async def update_user_ukr_group(telegram_id: int, ukr_group: str) -> None:
    """Оновлення підгрупи з української мови (5-8)."""
    conn = await get_db_connection()
    try:
        await conn.execute(
            "UPDATE users SET ukr_group = ?, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
            (ukr_group, telegram_id)
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


async def update_user_opp_group(telegram_id: int, opp_group: str) -> None:
    """Оновлення застарілої групи ОПП (для зворотної сумісності)."""
    conn = await get_db_connection()
    try:
        await conn.execute(
            "UPDATE users SET opp_group = ?, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
            (opp_group, telegram_id)
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
              AND (
                  prog_group IS NOT NULL
                  OR math_group IS NOT NULL
                  OR ukr_group IS NOT NULL
                  OR english_group IS NOT NULL
                  OR opp_group IS NOT NULL
              )
            """
        )
        rows = await cursor.fetchall()
        return [User.from_row(row) for row in rows]
    finally:
        await conn.close()
