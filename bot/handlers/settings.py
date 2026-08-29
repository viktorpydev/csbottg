from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from bot.database.models import (
    get_or_create_user,
    get_user,
    update_user_opp_group,
    update_user_english_group,
    update_user_notification_settings
)
from bot.keyboards.inline import (
    get_settings_keyboard,
    get_opp_groups_keyboard,
    get_english_groups_keyboard,
    get_notify_time_keyboard
)
from bot.services.schedule_service import schedule_service

router = Router()


@router.message(Command("settings"))
@router.message(F.text == "⚙️ Налаштування")
async def show_settings(message: Message):
    """Відображення меню налаштувань."""
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username
    )
    
    text = (
        "⚙️ <b>Панель налаштувань</b>\n\n"
        f"📚 Академічна група (ОПП): <b>{user.opp_group or 'Не обрано'}</b>\n"
        f"🇬🇧 Група з англійської: <b>{user.english_group or 'Не обрано'}</b>\n"
        f"⏰ Час нагадування: <b>за {user.notify_minutes} хв</b> до пари\n"
        f"🔔 Сповіщення: <b>{'Увімкнено' if user.notifications_enabled else 'Вимкнено'}</b>\n\n"
        "<i>Оберіть пункт нижче, щоб змінити налаштування:</i>"
    )
    await message.answer(text, reply_markup=get_settings_keyboard(user), parse_mode="HTML")


@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery):
    """Повернення до головної панелі налаштувань."""
    user = await get_user(callback.from_user.id)
    if not user:
        await callback.answer("Користувача не знайдено.")
        return

    text = (
        "⚙️ <b>Панель налаштувань</b>\n\n"
        f"📚 Академічна група (ОПП): <b>{user.opp_group or 'Не обрано'}</b>\n"
        f"🇬🇧 Група з англійської: <b>{user.english_group or 'Не обрано'}</b>\n"
        f"⏰ Час нагадування: <b>за {user.notify_minutes} хв</b> до пари\n"
        f"🔔 Сповіщення: <b>{'Увімкнено' if user.notifications_enabled else 'Вимкнено'}</b>\n\n"
        "<i>Оберіть пункт нижче, щоб змінити налаштування:</i>"
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_settings_keyboard(user),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "change_opp")
async def on_change_opp_clicked(callback: CallbackQuery):
    """Відображення списку груп ОПП для зміни."""
    user = await get_user(callback.from_user.id)
    current_opp = user.opp_group if user else None
    opp_groups = schedule_service.get_opp_groups()

    await callback.message.edit_text(
        "📚 <b>Оберіть вашу нову академічну групу (ОПП):</b>",
        reply_markup=get_opp_groups_keyboard(opp_groups, current=current_opp, prefix="settings_opp", show_back=True),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("settings_opp:"))
async def on_settings_opp_selected(callback: CallbackQuery):
    """Обробка вибору групи ОПП з налаштувань."""
    opp_group = callback.data.split(":", 1)[1]
    await update_user_opp_group(callback.from_user.id, opp_group)
    
    user = await get_user(callback.from_user.id)
    await callback.answer(f"✅ Академічну групу змінено на: {opp_group}")

    text = (
        "⚙️ <b>Панель налаштувань</b>\n\n"
        f"✅ <b>Академічну групу успішно змінено на {opp_group}!</b>\n\n"
        f"📚 Академічна група: <b>{user.opp_group}</b>\n"
        f"🇬🇧 Англійська: <b>{user.english_group or 'Не обрано'}</b>\n"
        f"⏰ Нагадування: <b>за {user.notify_minutes} хв</b>"
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_settings_keyboard(user),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "change_eng")
async def on_change_eng_clicked(callback: CallbackQuery):
    """Відображення списку підгруп з англійської для зміни."""
    user = await get_user(callback.from_user.id)
    current_eng = user.english_group if user else None
    eng_groups = schedule_service.get_english_groups()

    await callback.message.edit_text(
        "🇬🇧 <b>Оберіть вашу нову підгрупу з англійської мови:</b>",
        reply_markup=get_english_groups_keyboard(eng_groups, current=current_eng, prefix="settings_eng", show_back=True),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("settings_eng:"))
async def on_settings_eng_selected(callback: CallbackQuery):
    """Обробка вибору підгрупи з англійської з налаштувань."""
    eng_group = callback.data.split(":", 1)[1]
    await update_user_english_group(callback.from_user.id, eng_group)
    
    user = await get_user(callback.from_user.id)
    await callback.answer(f"✅ Групу з англійської змінено на: {eng_group}")

    text = (
        "⚙️ <b>Панель налаштувань</b>\n\n"
        f"✅ <b>Групу з англійської успішно змінено на {eng_group}!</b>\n\n"
        f"📚 Академічна група: <b>{user.opp_group or 'Не обрано'}</b>\n"
        f"🇬🇧 Англійська: <b>{user.english_group}</b>\n"
        f"⏰ Нагадування: <b>за {user.notify_minutes} хв</b>"
    )
    await callback.message.edit_text(
        text,
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
    await callback.answer(f"Час нагадування встановлено: за {minutes} хв!")
    
    text = (
        "⚙️ <b>Панель налаштувань</b>\n\n"
        f"✅ Час нагадування оновлено: <b>за {minutes} хв</b> до пари.\n\n"
        f"📚 Академічна група: <b>{user.opp_group}</b>\n"
        f"🇬🇧 Англійська: <b>{user.english_group}</b>"
    )
    await callback.message.edit_text(
        text,
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

    text = (
        "⚙️ <b>Панель налаштувань</b>\n\n"
        f"Статус сповіщень змінено на: <b>{status_str}</b>\n\n"
        f"📚 Академічна група: <b>{updated_user.opp_group}</b>\n"
        f"🇬🇧 Англійська: <b>{updated_user.english_group}</b>"
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_settings_keyboard(updated_user),
        parse_mode="HTML"
    )
