from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.database.models import User
from bot.services.schedule_service import parse_pe_slots


def _build_grid_keyboard(
    items: List[str],
    current: Optional[str] = None,
    prefix: str = "select",
    cols: int = 3,
    show_back: bool = False,
    back_callback: str = "back_to_settings"
) -> InlineKeyboardMarkup:
    """Універсальний генератор сітки інлайн-кнопок для вибору підгруп."""
    keyboard = []
    row = []
    for item in items:
        mark = " ✅" if current and str(item) == str(current) else ""
        row.append(InlineKeyboardButton(text=f"{item}{mark}", callback_data=f"{prefix}:{item}"))
        if len(row) == cols:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    if show_back:
        keyboard.append([InlineKeyboardButton(text="🔙 Назад до налаштувань", callback_data=back_callback)])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_prog_groups_keyboard(
    groups: List[str],
    current: Optional[str] = None,
    prefix: str = "select_prog",
    show_back: bool = False
) -> InlineKeyboardMarkup:
    """Генерація інлайн-клавіатури з групами мов програмування (1-6)."""
    return _build_grid_keyboard(groups, current=current, prefix=prefix, cols=3, show_back=show_back)


def get_math_groups_keyboard(
    groups: List[str],
    current: Optional[str] = None,
    prefix: str = "select_math",
    show_back: bool = False
) -> InlineKeyboardMarkup:
    """Генерація інлайн-клавіатури з групами математики (1-3)."""
    return _build_grid_keyboard(groups, current=current, prefix=prefix, cols=3, show_back=show_back)


def get_ukr_groups_keyboard(
    groups: List[str],
    current: Optional[str] = None,
    prefix: str = "select_ukr",
    show_back: bool = False
) -> InlineKeyboardMarkup:
    """Генерація інлайн-клавіатури з групами української мови (5-8)."""
    return _build_grid_keyboard(groups, current=current, prefix=prefix, cols=2, show_back=show_back)


def get_english_groups_keyboard(
    groups: List[str],
    current: Optional[str] = None,
    prefix: str = "select_eng",
    show_back: bool = False,
    show_skip: bool = False
) -> InlineKeyboardMarkup:
    """Генерація інлайн-клавіатури з доступними підгрупами з англійської (A53-A67)."""
    kb = _build_grid_keyboard(groups, current=current, prefix=prefix, cols=3, show_back=show_back)
    if show_skip:
        kb.inline_keyboard.append([
            InlineKeyboardButton(text="⏩ Пропустити (обрати пізніше)", callback_data=f"{prefix}:skip")
        ])
    return kb


def get_opp_groups_keyboard(
    groups: List[str],
    current: Optional[str] = None,
    prefix: str = "select_opp",
    show_back: bool = False
) -> InlineKeyboardMarkup:
    """Для зворотної сумісності зі старими викликами."""
    return get_prog_groups_keyboard(groups, current=current, prefix=prefix, show_back=show_back)


def get_settings_keyboard(user: User) -> InlineKeyboardMarkup:
    """Генерація інлайн-клавіатури налаштувань."""
    prog_text = user.prog_group or "Не обрано"
    math_text = user.math_group or "Не обрано"
    ukr_text = user.ukr_group or "Не обрано"
    eng_text = user.english_group or "Не обрано"
    notify_text = f"{user.notify_minutes} хв до пари"
    toggle_text = "🔔 Увімкнено" if user.notifications_enabled else "🔕 Вимкнено"
    mgmt_text = "Так ✅" if user.has_management else "Ні ❌"
    pe_list = parse_pe_slots(user.pe_slots)
    pe_text = f"Так ({len(pe_list)} пар) ✅" if pe_list else "Ні ❌"

    keyboard = [
        [
            InlineKeyboardButton(
                text=f"💻 Мови програмування (гр. {prog_text})",
                callback_data="change_prog"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📐 Математика (гр. {math_text})",
                callback_data="change_math"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🇺🇦 Українська мова (гр. {ukr_text})",
                callback_data="change_ukr"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🇬🇧 Англійська мова ({eng_text})",
                callback_data="change_eng"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"📊 Менеджмент: {mgmt_text}",
                callback_data="change_management"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"🏃 Фізвиховання: {pe_text}",
                callback_data="change_pe"
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


def get_management_keyboard(current: bool = False) -> InlineKeyboardMarkup:
    """Клавіатура вибору реєстрації на курс Менеджмент та персональна ефективність."""
    mark_yes = " ✅" if current else ""
    mark_no = " ✅" if not current else ""
    keyboard = [
        [
            InlineKeyboardButton(text=f"Так, я зареєстрований(-а){mark_yes}", callback_data="set_mgmt:1"),
        ],
        [
            InlineKeyboardButton(text=f"Ні, не реєструвався(-лась){mark_no}", callback_data="set_mgmt:0"),
        ],
        [
            InlineKeyboardButton(text="🔙 Назад до налаштувань", callback_data="back_to_settings")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_pe_initial_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура первинного питання про запис на фізвиховання."""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Так, записувався(-лась)", callback_data="set_pe_status:yes"),
        ],
        [
            InlineKeyboardButton(text="❌ Ні, не записувався(-лась)", callback_data="set_pe_status:no"),
        ],
        [
            InlineKeyboardButton(text="🔙 Назад до налаштувань", callback_data="back_to_settings")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_pe_menu_keyboard(has_slots: bool = False) -> InlineKeyboardMarkup:
    """Клавіатура головного меню керування заняттями з фізвиховання."""
    keyboard = [
        [
            InlineKeyboardButton(text="➕ Додати пару з фізвиховання", callback_data="pe_pick_day"),
        ]
    ]
    if has_slots:
        keyboard.append([
            InlineKeyboardButton(text="🗑️ Очистити всі мої пари", callback_data="pe_clear"),
        ])
    keyboard.append([
        InlineKeyboardButton(text="❌ Я більше не відвідую (Ні)", callback_data="set_pe_status:no"),
    ])
    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад до налаштувань", callback_data="back_to_settings")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_pe_days_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура вибору дня тижня для фізвиховання."""
    days = [
        ("Понеділок", 0),
        ("Вівторок", 1),
        ("Середа", 2),
        ("Четвер", 3),
        ("П'ятниця", 4),
        ("Субота", 5),
    ]
    keyboard = []
    row = []
    for name, d_idx in days:
        row.append(InlineKeyboardButton(text=name, callback_data=f"pe_day:{d_idx}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад до фізвиховання", callback_data="change_pe")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_pe_slots_keyboard(day_idx: int) -> InlineKeyboardMarkup:
    """Клавіатура вибору пари (часу) у вибраний день."""
    pairs = [
        ("1 пара (08:30)", "08:30"),
        ("2 пара (10:00)", "10:00"),
        ("3 пара (11:40)", "11:40"),
        ("4 пара (13:30)", "13:30"),
        ("5 пара (15:00)", "15:00"),
        ("6 пара (16:30)", "16:30"),
    ]
    keyboard = []
    row = []
    for label, time_str in pairs:
        row.append(InlineKeyboardButton(text=label, callback_data=f"pe_add_slot:{day_idx}:{time_str}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад до вибору дня", callback_data="pe_pick_day")
    ])
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
