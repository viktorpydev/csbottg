from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.database.models import User


def get_opp_groups_keyboard(
    groups: List[str],
    current: Optional[str] = None,
    prefix: str = "select_opp",
    show_back: bool = False
) -> InlineKeyboardMarkup:
    """Генерація інлайн-клавіатури з доступними групами ОПП."""
    keyboard = []
    row = []
    for g in groups:
        mark = " ✅" if current and g == current else ""
        row.append(InlineKeyboardButton(text=f"{g}{mark}", callback_data=f"{prefix}:{g}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    if show_back:
        keyboard.append([InlineKeyboardButton(text="🔙 Назад до налаштувань", callback_data="back_to_settings")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_english_groups_keyboard(
    groups: List[str],
    current: Optional[str] = None,
    prefix: str = "select_eng",
    show_back: bool = False
) -> InlineKeyboardMarkup:
    """Генерація інлайн-клавіатури з доступними підгрупами з англійської."""
    keyboard = []
    row = []
    for g in groups:
        mark = " ✅" if current and g == current else ""
        row.append(InlineKeyboardButton(text=f"{g}{mark}", callback_data=f"{prefix}:{g}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    if show_back:
        keyboard.append([InlineKeyboardButton(text="🔙 Назад до налаштувань", callback_data="back_to_settings")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_settings_keyboard(user: User) -> InlineKeyboardMarkup:
    """Генерація інлайн-клавіатури налаштувань."""
    opp_text = user.opp_group or "Не обрано"
    eng_text = user.english_group or "Не обрано"
    notify_text = f"{user.notify_minutes} хв до пари"
    toggle_text = "🔔 Увімкнено" if user.notifications_enabled else "🔕 Вимкнено"

    keyboard = [
        [
            InlineKeyboardButton(
                text=f"📚 Змінити групу ОПП ({opp_text})",
                callback_data="change_opp"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🇬🇧 Змінити англійську ({eng_text})",
                callback_data="change_eng"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"⏰ Час нагадування: {notify_text}",
                callback_data="change_notify_time"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Сповіщення: {toggle_text}",
                callback_data="toggle_notifications"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_notify_time_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для вибору часу заблагочасного нагадування."""
    times = [5, 10, 15, 20, 30, 45]
    keyboard = []
    row = []
    for t in times:
        row.append(InlineKeyboardButton(text=f"{t} хв", callback_data=f"set_notify:{t}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(text="🔙 Назад до налаштувань", callback_data="back_to_settings")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_week_pagination_keyboard(current_view_week: int, actual_current_week: int) -> InlineKeyboardMarkup:
    """Клавіатура для навігації між навчальними тижнями."""
    row_nav = []
    
    # Кнопка "Назад"
    if current_view_week > 1:
        row_nav.append(InlineKeyboardButton(text=f"⬅️ Тижд. {current_view_week - 1}", callback_data=f"view_week_num:{current_view_week - 1}"))

    # Кнопка поточності
    if current_view_week != actual_current_week:
        row_nav.append(InlineKeyboardButton(text=f"📍 Поточний ({actual_current_week})", callback_data=f"view_week_num:{actual_current_week}"))
    else:
        row_nav.append(InlineKeyboardButton(text=f"📍 {current_view_week}-й тижд. (зараз)", callback_data=f"view_week_num:{current_view_week}"))

    # Кнопка "Вперед"
    if current_view_week < 14:
        row_nav.append(InlineKeyboardButton(text=f"Тижд. {current_view_week + 1} ➡️", callback_data=f"view_week_num:{current_view_week + 1}"))

    keyboard = [
        row_nav,
        [
            InlineKeyboardButton(text="1️⃣ Непарний (1-й)", callback_data="view_week_num:1"),
            InlineKeyboardButton(text="2️⃣ Парний (2-й)", callback_data="view_week_num:2"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
