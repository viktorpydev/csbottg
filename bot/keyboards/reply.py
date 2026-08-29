from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Генерація головного меню reply-клавіатури."""
    keyboard = [
        [
            KeyboardButton(text="📅 Сьогодні"),
            KeyboardButton(text="🗓️ Завтра"),
        ],
        [
            KeyboardButton(text="📆 На тиждень"),
            KeyboardButton(text="⏳ Зараз"),
        ],
        [
            KeyboardButton(text="⚙️ Налаштування"),
            KeyboardButton(text="ℹ️ Допомога"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        persistent=True,
        input_field_placeholder="Оберіть пункт меню..."
    )
