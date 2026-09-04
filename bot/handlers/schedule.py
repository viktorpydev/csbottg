from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from bot.config import config
from bot.database.models import get_user
from bot.keyboards.inline import get_week_pagination_keyboard
from bot.services.schedule_service import schedule_service
from bot.services.week_service import get_week_info

router = Router()


async def check_user_configured(message: Message):
    """Допоміжна функція перевірки, чи обрав користувач свої підгрупи."""
    user = await get_user(message.from_user.id)
    has_all = bool(user and user.prog_group and user.math_group and user.ukr_group and user.english_group)
    has_legacy = bool(user and user.opp_group and user.english_group)

    if not user or not (has_all or has_legacy):
        await message.answer(
            "⚠️ <b>Ви ще не налаштували свої підгрупи!</b>\n\n"
            "Будь ласка, скористайтеся командою /start або перейдіть у ⚙️ <b>Налаштування</b>, щоб обрати підгрупи.",
            parse_mode="HTML"
        )
        return None
    return user


@router.message(Command("today"))
@router.message(F.text == "📅 Сьогодні")
async def show_today_schedule(message: Message):
    """Відображення розкладу на сьогодні."""
    user = await check_user_configured(message)
    if not user:
        return

    now = datetime.now(config.timezone)
    today = now.date()
    text = schedule_service.format_day_schedule(
        prog_group=user.prog_group,
        math_group=user.math_group,
        ukr_group=user.ukr_group,
        english_group=user.english_group,
        target_date=today,
        title_prefix="Розклад",
        opp_group=user.opp_group,
    )
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)


@router.message(Command("tomorrow"))
@router.message(F.text == "🗓️ Завтра")
async def show_tomorrow_schedule(message: Message):
    """Відображення розкладу на завтра."""
    user = await check_user_configured(message)
    if not user:
        return

    now = datetime.now(config.timezone)
    tomorrow = now.date() + timedelta(days=1)
    text = schedule_service.format_day_schedule(
        prog_group=user.prog_group,
        math_group=user.math_group,
        ukr_group=user.ukr_group,
        english_group=user.english_group,
        target_date=tomorrow,
        title_prefix="Розклад",
        opp_group=user.opp_group,
    )
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)


@router.message(Command("week"))
@router.message(F.text == "📆 На тиждень")
async def show_week_schedule(message: Message):
    """Відображення розкладу на поточний тиждень з кнопками навігації."""
    user = await check_user_configured(message)
    if not user:
        return

    now = datetime.now(config.timezone)
    today = now.date()
    week_info = get_week_info(today)

    text = schedule_service.format_week_schedule(
        prog_group=user.prog_group,
        math_group=user.math_group,
        ukr_group=user.ukr_group,
        english_group=user.english_group,
        target_date=today,
        week_number_override=week_info.week_number,
        opp_group=user.opp_group,
    )

    await message.answer(
        text,
        reply_markup=get_week_pagination_keyboard(
            current_view_week=week_info.week_number,
            actual_current_week=week_info.week_number
        ),
        parse_mode="HTML",
        disable_web_page_preview=True
    )


@router.callback_query(F.data.startswith("view_week_num:"))
async def toggle_week_num_view(callback: CallbackQuery):
    """Перегляд розкладу для конкретного номера навчального тижня."""
    user = await get_user(callback.from_user.id)
    has_all = bool(user and user.prog_group and user.math_group and user.ukr_group and user.english_group)
    has_legacy = bool(user and user.opp_group and user.english_group)

    if not user or not (has_all or has_legacy):
        await callback.answer("Спочатку оберіть підгрупи у налаштуваннях!", show_alert=True)
        return

    target_week_num = int(callback.data.split(":", 1)[1])
    now = datetime.now(config.timezone)
    today = now.date()
    current_week_info = get_week_info(today)

    text = schedule_service.format_week_schedule(
        prog_group=user.prog_group,
        math_group=user.math_group,
        ukr_group=user.ukr_group,
        english_group=user.english_group,
        target_date=today,
        week_number_override=target_week_num,
        opp_group=user.opp_group,
    )

    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_week_pagination_keyboard(
                current_view_week=target_week_num,
                actual_current_week=current_week_info.week_number
            ),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        await callback.answer(f"Відображено {target_week_num}-й тиждень")
    except Exception:
        await callback.answer(f"Відображено {target_week_num}-й тиждень")


@router.message(Command("now"))
@router.message(F.text == "⏳ Зараз")
async def show_now_status(message: Message):
    """Відображення поточної та наступної пари."""
    user = await check_user_configured(message)
    if not user:
        return

    now = datetime.now(config.timezone)
    text = schedule_service.format_now_schedule(
        prog_group=user.prog_group,
        math_group=user.math_group,
        ukr_group=user.ukr_group,
        english_group=user.english_group,
        current_dt=now,
        opp_group=user.opp_group,
    )
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)
