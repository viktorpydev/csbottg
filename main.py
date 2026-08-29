import asyncio
import logging
import sys

try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from bot.config import config
from bot.database.db import init_db
from bot.handlers import get_main_router
from bot.services.scheduler import setup_scheduler
from bot.services.web_server import start_web_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("bot")


async def set_bot_commands(bot: Bot):
    """Реєстрація команд бота у меню Telegram."""
    commands = [
        BotCommand(command="today", description="📅 Розклад на сьогодні"),
        BotCommand(command="tomorrow", description="🗓️ Розклад на завтра"),
        BotCommand(command="week", description="📆 Розклад на тиждень"),
        BotCommand(command="now", description="⏳ Зараз / Наступна пара"),
        BotCommand(command="settings", description="⚙️ Налаштування груп та нагадувань"),
        BotCommand(command="help", description="ℹ️ Довідка щодо використання"),
        BotCommand(command="start", description="🔄 Перезапуск / Вибір груп"),
    ]
    await bot.set_my_commands(commands)


async def main():
    logger.info("Starting Telegram Schedule Bot...")

    if config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not config.BOT_TOKEN:
        logger.warning(
            "⚠️ BOT_TOKEN is not set or using default placeholder! "
            "Please create a .env file or set BOT_TOKEN environment variable."
        )

    # 1. Ініціалізація бази даних SQLite
    await init_db()

    # 2. Ініціалізація бота та диспетчера
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # 3. Підключення обробників (хендлерів)
    dp.include_router(get_main_router())

    # 4. Налаштування команд бота
    try:
        await set_bot_commands(bot)
    except Exception as e:
        logger.warning(f"Could not set bot commands automatically: {e}")

    # 5. Налаштування фонового планувальника нагадувань
    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Background reminder scheduler started.")

    # 6. Запуск мінімального веб-сервера (якщо увімкнено)
    web_runner = None
    if config.WEB_ENABLED:
        try:
            web_runner = await start_web_server(config.WEB_HOST, config.effective_web_port)
        except Exception as e:
            logger.error(f"Failed to start web server: {e}")

    try:
        # Видалення застарілих оновлень та запуск опитування
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot polling started. Press Ctrl+C to stop.")
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down bot...")
        if web_runner:
            await web_runner.cleanup()
            logger.info("Web server stopped.")
        scheduler.shutdown(wait=False)
        await bot.session.close()
        logger.info("Bot stopped successfully.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user.")
