import asyncio
import logging
from datetime import datetime, timedelta
from typing import Set, Tuple
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.config import config
from bot.database.models import get_all_active_users
from bot.services.schedule_service import schedule_service

logger = logging.getLogger(__name__)

# Кеш надісланих сповіщень: (user_telegram_id, lesson_id, date_str)
sent_notifications: Set[Tuple[int, str, str]] = set()


async def check_and_send_reminders(bot: Bot):
    """
    Періодична задача, що перевіряє, чи є у користувача пара, яка незабаром починається,
    та надсилає сповіщення відповідно до його налаштувань.
    """
    try:
        now = datetime.now(config.timezone)
        today = now.date()
        today_str = today.isoformat()
        current_time_minutes = now.hour * 60 + now.minute

        # Очищення вчорашніх записів у кеші
        keys_to_remove = [key for key in sent_notifications if key[2] != today_str]
        for key in keys_to_remove:
            sent_notifications.remove(key)

        users = await get_all_active_users()
        if not users:
            return

        for user in users:
            if not user.opp_group or not user.english_group or not user.notifications_enabled:
                continue

            notify_advance = user.notify_minutes if user.notify_minutes is not None else config.DEFAULT_NOTIFY_MINUTES
            
            _, lessons = schedule_service.get_lessons_for_date(
                opp_group=user.opp_group,
                english_group=user.english_group,
                target_date=today
            )

            for lesson in lessons:
                start_h, start_m = map(int, lesson.start_time.split(":"))
                lesson_start_minutes = start_h * 60 + start_m
                diff = lesson_start_minutes - current_time_minutes
                # Спрацьовує, якщо пара починається у найближчі хвилини (в межах notify_advance) і нагадування ще не надсилалося
                if 0 < diff <= notify_advance:
                    cache_key = (user.telegram_id, lesson.id, today_str)
                    if cache_key in sent_notifications:
                        continue

                    msg_text = schedule_service.format_reminder_message(lesson, minutes_left=diff)
                    try:
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=msg_text,
                            parse_mode="HTML",
                            disable_web_page_preview=True
                        )
                        sent_notifications.add(cache_key)
                        logger.info(f"Sent reminder for lesson '{lesson.subject}' to user {user.telegram_id}")
                    except Exception as err:
                        logger.warning(f"Failed to send reminder to user {user.telegram_id}: {err}")
    except Exception as e:
        logger.exception(f"Error in check_and_send_reminders job: {e}")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Налаштування та запуск AsyncIOScheduler."""
    scheduler = AsyncIOScheduler(timezone=config.timezone)
    scheduler.add_job(
        check_and_send_reminders,
        "interval",
        seconds=60,
        args=[bot],
        id="schedule_reminder_job",
        replace_existing=True,
    )
    return scheduler
