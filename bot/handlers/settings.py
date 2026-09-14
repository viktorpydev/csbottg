import json
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
    update_user_management,
    update_user_pe_slots,
    User
)
from bot.keyboards.inline import (
    get_settings_keyboard,
    get_prog_groups_keyboard,
    get_math_groups_keyboard,
    get_ukr_groups_keyboard,
    get_english_groups_keyboard,
    get_notify_time_keyboard,
    get_management_keyboard,
    get_pe_initial_keyboard,
    get_pe_menu_keyboard,
    get_pe_days_keyboard,
    get_pe_slots_keyboard,
)
from bot.services.schedule_service import schedule_service, parse_pe_slots, PAIR_TIME_MAP
from bot.services.week_service import UKRAINIAN_WEEKDAYS

router = Router()


def _render_settings_text(user: User, success_notice: str = "") -> str:
    """Форматування тексту головного меню налаштувань."""
    prog_text = f"група {user.prog_group}" if user.prog_group else "Не обрано"
    math_text = f"група {user.math_group}" if user.math_group else "Не обрано"
    ukr_text = f"група {user.ukr_group}" if user.ukr_group else "Не обрано"
    eng_text = user.english_group or "Не обрано"
    mgmt_text = "Зареєстрований(-а) ✅" if user.has_management else "Не реєструвався(-лась) ❌"
    pe_list = parse_pe_slots(user.pe_slots)
    pe_text = f"Записаний(-а) ({len(pe_list)} пар) ✅" if pe_list else "Не відвідую ❌"
    status_str = "Увімкнено 🔔" if user.notifications_enabled else "Вимкнено 🔕"

    notice_part = f"{success_notice}\n\n" if success_notice else ""

    return (
        f"⚙️ <b>Панель налаштувань</b>\n\n"
        f"{notice_part}"
        f"💻 Мови програмування: <b>{prog_text}</b>\n"
        f"📐 Математика: <b>{math_text}</b>\n"
        f"🇺🇦 Українська мова: <b>{ukr_text}</b>\n"
        f"🇬🇧 Англійська мова: <b>{eng_text}</b>\n"
        f"📊 Менеджмент: <b>{mgmt_text}</b>\n"
        f"🏃 Фізичне виховання: <b>{pe_text}</b>\n"
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


# --- Налаштування курсу "Менеджмент та персональна ефективність" ---

@router.callback_query(F.data == "change_management")
async def on_change_management_clicked(callback: CallbackQuery):
    """Відображення питання щодо курсу Менеджмент та персональна ефективність."""
    user = await get_user(callback.from_user.id)
    has_mgmt = user.has_management if user else False
    text = (
        "📊 <b>Менеджмент та персональна ефективність</b>\n\n"
        "<b>Чи реєструвались ви на цей курс?</b>\n\n"
        "▫️ Заняття проходять у понеділок (16:30) та суботу (13:30) на 3–5 тижнях.\n"
        "▫️ Якщо ви зареєстровані, курс буде додано до вашого розкладу та нагадувань.\n"
        "▫️ Якщо ні — ці пари не відображатимуться."
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_management_keyboard(current=has_mgmt),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_mgmt:"))
async def on_set_management(callback: CallbackQuery):
    """Обробка вибору реєстрації на Менеджмент."""
    val = callback.data.split(":", 1)[1] == "1"
    await update_user_management(callback.from_user.id, val)

    user = await get_user(callback.from_user.id)
    msg = "✅ Менеджмент додано до розкладу!" if val else "❌ Менеджмент приховано з розкладу."
    await callback.answer(msg)
    await callback.message.edit_text(
        _render_settings_text(user, success_notice=msg),
        reply_markup=get_settings_keyboard(user),
        parse_mode="HTML"
    )


# --- Налаштування Фізичного виховання ---

def _render_pe_menu_text(user: User) -> str:
    """Форматування тексту меню фізичного виховання."""
    pe_list = parse_pe_slots(user.pe_slots)
    if not pe_list:
        return (
            "🏃 <b>Фізичне виховання</b>\n\n"
            "<b>Чи записувались ви на фізичне виховання?</b>\n\n"
            "Якщо ви обрали секцію та пари з фізвиховання, натисніть <b>«Так»</b>, "
            "щоб вказати дні та час ваших занять для розкладу та нагадувань.\n\n"
            "Якщо ви не записувались або маєте звільнення — оберіть <b>«Ні»</b>."
        )
    slots_lines = []
    for idx, s in enumerate(pe_list, 1):
        d_idx = int(s.get("day_of_week", 0))
        d_name = UKRAINIAN_WEEKDAYS[d_idx] if 0 <= d_idx < len(UKRAINIAN_WEEKDAYS) else "День"
        st = s.get("start_time", "08:30")
        et = s.get("end_time") or PAIR_TIME_MAP.get(st, "09:50")
        slots_lines.append(f"  {idx}. <b>{d_name}</b>: <code>{st} - {et}</code> (Спорткомплекс)")
    slots_block = "\n".join(slots_lines)
    return (
        "🏃 <b>Ваші заняття з фізичного виховання:</b>\n\n"
        f"{slots_block}\n\n"
        "<i>Ви можете додати ще одну пару, очистити список або вказати, що не відвідуєте:</i>"
    )


@router.callback_query(F.data == "change_pe")
async def on_change_pe_clicked(callback: CallbackQuery):
    """Відображення меню керування фізичним вихованням."""
    user = await get_user(callback.from_user.id)
    pe_list = parse_pe_slots(user.pe_slots) if user else []

    if pe_list:
        await callback.message.edit_text(
            _render_pe_menu_text(user),
            reply_markup=get_pe_menu_keyboard(has_slots=True),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            _render_pe_menu_text(user),
            reply_markup=get_pe_initial_keyboard(),
            parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data == "set_pe_status:no")
async def on_set_pe_no(callback: CallbackQuery):
    """Користувач обрав 'Ні' для фізвиховання."""
    await update_user_pe_slots(callback.from_user.id, None)
    user = await get_user(callback.from_user.id)
    await callback.answer("Фізичне виховання приховано")
    await callback.message.edit_text(
        _render_settings_text(user, success_notice="❌ Фізичне виховання вимкнено з розкладу."),
        reply_markup=get_settings_keyboard(user),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "set_pe_status:yes")
async def on_set_pe_yes(callback: CallbackQuery):
    """Користувач обрав 'Так' для фізвиховання."""
    user = await get_user(callback.from_user.id)
    await callback.answer()
    await callback.message.edit_text(
        _render_pe_menu_text(user),
        reply_markup=get_pe_menu_keyboard(has_slots=False),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "pe_pick_day")
async def on_pe_pick_day(callback: CallbackQuery):
    """Вибір дня тижня для фізвиховання."""
    await callback.message.edit_text(
        "🏃 <b>Оберіть день тижня, коли у вас проходить фізвиховання:</b>",
        reply_markup=get_pe_days_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pe_day:"))
async def on_pe_day_selected(callback: CallbackQuery):
    """Вибір пари (часу) у вибраний день."""
    day_idx = int(callback.data.split(":", 1)[1])
    day_name = UKRAINIAN_WEEKDAYS[day_idx]
    await callback.message.edit_text(
        f"🏃 <b>Оберіть номер пари у день: {day_name}</b>",
        reply_markup=get_pe_slots_keyboard(day_idx),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pe_add_slot:"))
async def on_pe_slot_added(callback: CallbackQuery):
    """Додавання обраного слота пари до списку занять користувача."""
    parts = callback.data.split(":")
    day_idx = int(parts[1])
    start_time = parts[2]
    end_time = PAIR_TIME_MAP.get(start_time, "09:50")

    user = await get_user(callback.from_user.id)
    slots = parse_pe_slots(user.pe_slots) if user else []

    already_added = any(s.get("day_of_week") == day_idx and s.get("start_time") == start_time for s in slots)
    if not already_added:
        slots.append({
            "day_of_week": day_idx,
            "start_time": start_time,
            "end_time": end_time
        })
        slots.sort(key=lambda s: (int(s.get("day_of_week", 0)), s.get("start_time", "")))
        await update_user_pe_slots(callback.from_user.id, json.dumps(slots, ensure_ascii=False))
        user = await get_user(callback.from_user.id)
        day_name = UKRAINIAN_WEEKDAYS[day_idx]
        await callback.answer(f"✅ Додано: {day_name} {start_time}")
    else:
        await callback.answer("Ця пара вже додана до вашого списку!")

    await callback.message.edit_text(
        _render_pe_menu_text(user),
        reply_markup=get_pe_menu_keyboard(has_slots=True),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "pe_clear")
async def on_pe_clear(callback: CallbackQuery):
    """Очищення всіх обраних пар з фізвиховання."""
    await update_user_pe_slots(callback.from_user.id, None)
    user = await get_user(callback.from_user.id)
    await callback.answer("Усі пари з фізвиховання очищено")
    await callback.message.edit_text(
        _render_pe_menu_text(user),
        reply_markup=get_pe_initial_keyboard(),
        parse_mode="HTML"
    )
