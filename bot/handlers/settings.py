from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from bot.database.models import (
    get_or_create_user,
    get_user,
    update_user_prog_group,
    update_user_math_group,
    update_user_ukr_group,
    update_user_english_group,
    update_user_notification_settings,
    User
)
from bot.keyboards.inline import (
    get_settings_keyboard,
    get_prog_groups_keyboard,
    get_math_groups_keyboard,
    get_ukr_groups_keyboard,
    get_english_groups_keyboard,
    get_notify_time_keyboard
)
from bot.services.schedule_service import schedule_service

router = Router()


def _render_settings_text(user: User, success_notice: str = "") -> str:
    """Форматування тексту головного меню налаштувань."""
    prog_text = f"група {user.prog_group}" if user.prog_group else "Не обрано"
    math_text = f"група {user.math_group}" if user.math_group else "Не обрано"
    ukr_text = f"група {user.ukr_group}" if user.ukr_group else "Не обрано"
    eng_text = user.english_group or "Не обрано"
    status_str = "Увімкнено 🔔" if user.notifications_enabled else "Вимкнено 🔕"

    notice_part = f"{success_notice}\n\n" if success_notice else ""

    return (
        f"⚙️ <b>Панель налаштувань</b>\n\n"
        f"{notice_part}"
        f"💻 Мови програмування: <b>{prog_text}</b>\n"
        f"📐 Математика: <b>{math_text}</b>\n"
        f"🇺🇦 Українська мова: <b>{ukr_text}</b>\n"
        f"🇬🇧 Англійська мова: <b>{eng_text}</b>\n"
        f"⏰ Час нагадування: <b>за {user.notify_minutes} хв</b> до пари\n"
        f"🔔 Сповіщення: <b>{status_str}</b>\n\n"
        f"<i>Оберіть пункт нижче, щоб змінити налаштування:</i>"
    )


@router.message(Command("settings"))
@router.message(F.text == "⚙️ Налаштування")
async def show_settings(message: Message):
    """Відображення меню налаштувань."""
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username
    )
    await message.answer(_render_settings_text(user), reply_markup=get_settings_keyboard(user), parse_mode="HTML")


@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery):
    """Повернення до головної панелі налаштувань."""
    user = await get_user(callback.from_user.id)
    if not user:
        await callback.answer("Користувача не знайдено.")
        return

    await callback.message.edit_text(
        _render_settings_text(user),
        reply_markup=get_settings_keyboard(user),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "change_prog")
async def on_change_prog_clicked(callback: CallbackQuery):
    """Відображення вибору підгрупи з програмування."""
    user = await get_user(callback.from_user.id)
    current = user.prog_group if user else None
    groups = schedule_service.get_prog_groups()

    await callback.message.edit_text(
        "💻 <b>Оберіть вашу підгрупу з Мов програмування (1–6):</b>",
        reply_markup=get_prog_groups_keyboard(groups, current=current, prefix="settings_prog", show_back=True),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("settings_prog:"))
async def on_settings_prog_selected(callback: CallbackQuery):
    """Обробка збереження обраної групи з програмування."""
    prog_group = callback.data.split(":", 1)[1]
    await update_user_prog_group(callback.from_user.id, prog_group)

    user = await get_user(callback.from_user.id)
    await callback.answer(f"✅ Програмування: група {prog_group}")
    await callback.message.edit_text(
        _render_settings_text(user, success_notice=f"✅ Групу з програмування змінено на <b>{prog_group}</b>!"),
        reply_markup=get_settings_keyboard(user),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "change_math")
async def on_change_math_clicked(callback: CallbackQuery):
    """Відображення вибору підгрупи з математики."""
    user = await get_user(callback.from_user.id)
    current = user.math_group if user else None
    groups = schedule_service.get_math_groups()

    await callback.message.edit_text(
        "📐 <b>Оберіть вашу підгрупу з Математики (1–3):</b>",
        reply_markup=get_math_groups_keyboard(groups, current=current, prefix="settings_math", show_back=True),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("settings_math:"))
async def on_settings_math_selected(callback: CallbackQuery):
    """Обробка збереження обраної групи з математики."""
    math_group = callback.data.split(":", 1)[1]
    await update_user_math_group(callback.from_user.id, math_group)

    user = await get_user(callback.from_user.id)
    await callback.answer(f"✅ Математика: група {math_group}")
    await callback.message.edit_text(
        _render_settings_text(user, success_notice=f"✅ Групу з математики змінено на <b>{math_group}</b>!"),
        reply_markup=get_settings_keyboard(user),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "change_ukr")
async def on_change_ukr_clicked(callback: CallbackQuery):
    """Відображення вибору підгрупи з української мови."""
    user = await get_user(callback.from_user.id)
    current = user.ukr_group if user else None
    groups = schedule_service.get_ukr_groups()

    await callback.message.edit_text(
        "🇺🇦 <b>Оберіть вашу підгрупу з Української мови (5–8):</b>",
        reply_markup=get_ukr_groups_keyboard(groups, current=current, prefix="settings_ukr", show_back=True),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("settings_ukr:"))
async def on_settings_ukr_selected(callback: CallbackQuery):
    """Обробка збереження обраної групи з української мови."""
    ukr_group = callback.data.split(":", 1)[1]
    await update_user_ukr_group(callback.from_user.id, ukr_group)

    user = await get_user(callback.from_user.id)
    await callback.answer(f"✅ Українська мова: група {ukr_group}")
    await callback.message.edit_text(
        _render_settings_text(user, success_notice=f"✅ Групу з укр. мови змінено на <b>{ukr_group}</b>!"),
        reply_markup=get_settings_keyboard(user),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "change_eng")
async def on_change_eng_clicked(callback: CallbackQuery):
    """Відображення списку підгруп з англійської для зміни."""
    user = await get_user(callback.from_user.id)
    current = user.english_group if user else None
    groups = schedule_service.get_english_groups()

    await callback.message.edit_text(
        "🇬🇧 <b>Оберіть вашу нову підгрупу з англійської мови:</b>",
        reply_markup=get_english_groups_keyboard(groups, current=current, prefix="settings_eng", show_back=True),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("settings_eng:"))
async def on_settings_eng_selected(callback: CallbackQuery):
    """Обробка вибору підгрупи з англійської з налаштувань."""
    eng_group = callback.data.split(":", 1)[1]
    await update_user_english_group(callback.from_user.id, eng_group)

    user = await get_user(callback.from_user.id)
    await callback.answer(f"✅ Англійська: {eng_group}")
    await callback.message.edit_text(
        _render_settings_text(user, success_notice=f"✅ Групу з англійської успішно змінено на <b>{eng_group}</b>!"),
        reply_markup=get_settings_keyboard(user),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "change_notify_time")
async def on_change_notify_time_clicked(callback: CallbackQuery):
    """Відображення вибору часу заблагочасного сповіщення."""
    await callback.message.edit_text(
        "⏰ <b>Оберіть, за скільки хвилин до початку пари надсилати нагадування:</b>",
        reply_markup=get_notify_time_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_notify:"))
async def on_notify_time_set(callback: CallbackQuery):
    """Збереження обраного часу заблагочасного сповіщення."""
    minutes = int(callback.data.split(":", 1)[1])
    await update_user_notification_settings(callback.from_user.id, notify_minutes=minutes)

    user = await get_user(callback.from_user.id)
    await callback.answer(f"Час нагадування: за {minutes} хв!")
    await callback.message.edit_text(
        _render_settings_text(user, success_notice=f"✅ Час нагадування оновлено: <b>за {minutes} хв</b> до пари."),
        reply_markup=get_settings_keyboard(user),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "toggle_notifications")
async def on_toggle_notifications(callback: CallbackQuery):
    """Перемикання увімкнення/вимкнення сповіщень."""
    user = await get_user(callback.from_user.id)
    if not user:
        return

    new_state = not user.notifications_enabled
    await update_user_notification_settings(callback.from_user.id, notifications_enabled=new_state)

    updated_user = await get_user(callback.from_user.id)
    status_str = "увімкнено 🔔" if new_state else "вимкнено 🔕"
    await callback.answer(f"Сповіщення {status_str}")
    await callback.message.edit_text(
        _render_settings_text(updated_user, success_notice=f"✅ Сповіщення <b>{status_str}</b>."),
        reply_markup=get_settings_keyboard(updated_user),
        parse_mode="HTML"
    )
