import pytest
import pytest_asyncio
from pathlib import Path
from bot.config import config
from bot.database.db import init_db
from bot.database.models import (
    get_or_create_user,
    get_user,
    update_user_opp_group,
    update_user_english_group,
    update_user_notification_settings,
    get_all_active_users
)


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db(tmp_path: Path):
    test_db = tmp_path / "test_bot.sqlite3"
    config.DATABASE_PATH = test_db
    await init_db()
    yield
    if test_db.exists():
        try:
            test_db.unlink()
        except PermissionError:
            pass


@pytest.mark.asyncio
async def test_user_creation_and_retrieval():
    user = await get_or_create_user(
        telegram_id=11223344,
        full_name="Тестовий Студент",
        username="test_student"
    )
    assert user.telegram_id == 11223344
    assert user.full_name == "Тестовий Студент"
    assert user.opp_group is None
    assert user.english_group is None
    assert user.notify_minutes == 10
    assert user.notifications_enabled is True

    # Повторне отримання
    fetched = await get_user(11223344)
    assert fetched is not None
    assert fetched.telegram_id == 11223344


@pytest.mark.asyncio
async def test_update_groups_and_notifications():
    await get_or_create_user(telegram_id=998877, full_name="User 2", username="user2")
    
    await update_user_opp_group(998877, "ІПЗ-21")
    await update_user_english_group(998877, "Eng-B2.1")
    await update_user_notification_settings(998877, notify_minutes=15, notifications_enabled=True)

    user = await get_user(998877)
    assert user.opp_group == "ІПЗ-21"
    assert user.english_group == "Eng-B2.1"
    assert user.notify_minutes == 15
    assert user.notifications_enabled is True

    # Перевірка списку активних користувачів
    active_users = await get_all_active_users()
    assert any(u.telegram_id == 998877 for u in active_users)

    # Вимкнення сповіщень
    await update_user_notification_settings(998877, notifications_enabled=False)
    active_users_after = await get_all_active_users()
    assert not any(u.telegram_id == 998877 for u in active_users_after)
