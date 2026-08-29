"""Пакет хендлерів (обробників)."""
from aiogram import Router
from bot.handlers.start import router as start_router
from bot.handlers.schedule import router as schedule_router
from bot.handlers.settings import router as settings_router
from bot.handlers.common import router as common_router


def get_main_router() -> Router:
    """Об'єднання всіх роутерів."""
    main_router = Router()
    main_router.include_router(start_router)
    main_router.include_router(schedule_router)
    main_router.include_router(settings_router)
    main_router.include_router(common_router)
    return main_router
