import pytest
import pytest_asyncio
from pathlib import Path
from bot.config import config
from bot.database.db import init_db
from bot.database.models import (
    get_or_create_user,
    get_user,
    update_user_prog_group,
    update_user_math_group,
    update_user_ukr_group,
    update_user_english_group,
    update_user_opp_group,
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
    assert user.prog_group is None
    assert user.math_group is None
    assert user.ukr_group is None
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

    await update_user_prog_group(998877, "2")
    await update_user_math_group(998877, "1")
    await update_user_ukr_group(998877, "6")
    await update_user_english_group(998877, "A55")
    await update_user_notification_settings(998877, notify_minutes=15, notifications_enabled=True)

    user = await get_user(998877)
    assert user.prog_group == "2"
    assert user.math_group == "1"
    assert user.ukr_group == "6"
    assert user.english_group == "A55"
    assert user.notify_minutes == 15
    assert user.notifications_enabled is True

    # Перевірка списку активних користувачів
    active_users = await get_all_active_users()
    assert any(u.telegram_id == 998877 for u in active_users)

    # Вимкнення сповіщень
    await update_user_notification_settings(998877, notifications_enabled=False)
    active_users_after = await get_all_active_users()
    assert not any(u.telegram_id == 998877 for u in active_users_after)


@pytest.mark.asyncio
async def test_legacy_opp_support():
    await get_or_create_user(telegram_id=555444, full_name="User Legacy", username="legacy")
    await update_user_opp_group(555444, "КН-1")
    await update_user_english_group(555444, "A53")
    user = await get_user(555444)
    assert user.opp_group == "КН-1"
    active_users = await get_all_active_users()
    assert any(u.telegram_id == 555444 for u in active_users)


@pytest.mark.asyncio
async def test_partial_groups_active_user():
    # Користувач, який обрав тільки мови програмування та математику, але ще не обрав англійську
    await get_or_create_user(telegram_id=123987, full_name="Partial User", username="partial")
    await update_user_prog_group(123987, "2")
    await update_user_math_group(123987, "1")
    await update_user_ukr_group(123987, "5")

    user = await get_user(123987)
    assert user.english_group is None
    assert user.prog_group == "2"

    active_users = await get_all_active_users()
    assert any(u.telegram_id == 123987 for u in active_users)

