from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from bot.database.models import (
    get_or_create_user,
    update_user_opp_group,
    update_user_english_group
)
from bot.keyboards.inline import (
    get_opp_groups_keyboard,
    get_english_groups_keyboard
)
from bot.keyboards.reply import get_main_menu_keyboard
from bot.services.schedule_service import schedule_service
from bot.services.week_service import format_week_header

router = Router()


class RegistrationState(StatesGroup):
    choosing_opp = State()
    choosing_english = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обробка команди /start."""
    await state.clear()
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username
    )

    week_status = format_week_header()

    if user.opp_group and user.english_group:
        welcome_text = (
            f"👋 <b>Привіт, {message.from_user.first_name}!</b>\n\n"
            f"{week_status}\n\n"
            f"📌 <b>Ваші поточні налаштування:</b>\n"
            f"   ▫️ ОПП група: <b>{user.opp_group}</b>\n"
            f"   ▫️ Група з англійської: <b>{user.english_group}</b>\n"
            f"   ▫️ Нагадування: <b>{user.notify_minutes} хв</b> до пари ({'🔔 увімкнено' if user.notifications_enabled else '🔕 вимкнено'})\n\n"
            f"Використовуйте кнопки меню нижче для перегляду розкладу або налаштувань. 👇"
        )
        await message.answer(
            welcome_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        # Користувачу потрібне початкове налаштування
        opp_groups = schedule_service.get_opp_groups()
        await state.set_state(RegistrationState.choosing_opp)
        
        intro_text = (
            f"👋 <b>Вітаю у боті розкладу та нагадувань!</b>\n\n"
            f"{week_status}\n\n"
            f"Щоб сформувати персональний розклад та отримувати своєчасні сповіщення, давайте оберемо ваші групи.\n\n"
            f"👉 <b>Крок 1/2: Оберіть вашу основну академічну групу (ОПП):</b>"
        )
        await message.answer(
            intro_text,
            reply_markup=get_opp_groups_keyboard(opp_groups),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("select_opp:"))
async def on_opp_selected(callback: CallbackQuery, state: FSMContext):
    """Обробка вибору групи ОПП."""
    opp_group = callback.data.split(":", 1)[1]
    await update_user_opp_group(callback.from_user.id, opp_group)
    
    eng_groups = schedule_service.get_english_groups()
    await state.set_state(RegistrationState.choosing_english)
    
    await callback.answer(f"Обрано: {opp_group}")
    await callback.message.edit_text(
        f"✅ Основна група: <b>{opp_group}</b>\n\n"
        f"👉 <b>Крок 2/2: Тепер оберіть вашу підгрупу з англійської мови:</b>",
        reply_markup=get_english_groups_keyboard(eng_groups),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("select_eng:"))
async def on_english_selected(callback: CallbackQuery, state: FSMContext):
    """Обробка вибору підгрупи з англійської."""
    eng_group = callback.data.split(":", 1)[1]
    await update_user_english_group(callback.from_user.id, eng_group)
    await state.clear()

    user = await get_or_create_user(callback.from_user.id)
    await callback.answer(f"Обрано: {eng_group}")

    finish_text = (
        f"🎉 <b>Налаштування успішно завершено!</b>\n\n"
        f"📚 ОПП група: <b>{user.opp_group}</b>\n"
        f"🇬🇧 Англійська: <b>{user.english_group}</b>\n"
        f"🔔 Нагадування: <b>за {user.notify_minutes} хв</b> до кожної пари.\n\n"
        f"Тепер ви можете переглядати свій розклад через меню нижче."
    )

    await callback.message.edit_text(
        finish_text,
        parse_mode="HTML"
    )

    await callback.message.answer(
        "Оберіть дію в головному меню:",
        reply_markup=get_main_menu_keyboard()
    )
