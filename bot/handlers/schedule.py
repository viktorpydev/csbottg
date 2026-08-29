from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from bot.config import config
from bot.database.models import get_user
from bot.keyboards.inline import get_week_pagination_keyboard, get_opp_groups_keyboard
from bot.services.schedule_service import schedule_service
from bot.services.week_service import get_week_info

router = Router()


async def check_user_configured(message: Message):
    """Допоміжна функція перевірки, чи обрав користувач свої групи."""
    user = await get_user(message.from_user.id)
    if not user or not user.opp_group or not user.english_group:
        opp_groups = schedule_service.get_opp_groups()
        await message.answer(
            "⚠️ <b>Ви ще не налаштували свої групи!</b>\n\n"
            "Будь ласка, оберіть вашу основну групу ОПП:",
            reply_markup=get_opp_groups_keyboard(opp_groups),
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
        opp_group=user.opp_group,
        english_group=user.english_group,
        target_date=today,
        title_prefix="Розклад"
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
        opp_group=user.opp_group,
        english_group=user.english_group,
        target_date=tomorrow,
        title_prefix="Розклад"
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
        opp_group=user.opp_group,
        english_group=user.english_group,
        target_date=today,
        week_number_override=week_info.week_number
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
    if not user or not user.opp_group or not user.english_group:
        await callback.answer("Спочатку оберіть групу!", show_alert=True)
        return

    target_week_num = int(callback.data.split(":", 1)[1])
    now = datetime.now(config.timezone)
    today = now.date()
    current_week_info = get_week_info(today)

    text = schedule_service.format_week_schedule(
        opp_group=user.opp_group,
        english_group=user.english_group,
        target_date=today,
        week_number_override=target_week_num
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
        opp_group=user.opp_group,
        english_group=user.english_group,
        current_dt=now
    )
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)
