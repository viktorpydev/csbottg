from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from bot.database.models import (
    get_or_create_user,
    update_user_prog_group,
    update_user_math_group,
    update_user_ukr_group,
    update_user_english_group
)
from bot.keyboards.inline import (
    get_prog_groups_keyboard,
    get_math_groups_keyboard,
    get_ukr_groups_keyboard,
    get_english_groups_keyboard
)
from bot.keyboards.reply import get_main_menu_keyboard
from bot.services.schedule_service import schedule_service
from bot.services.week_service import format_week_header

router = Router()


class RegistrationState(StatesGroup):
    choosing_prog = State()
    choosing_math = State()
    choosing_ukr = State()
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
    is_configured = bool(user and (user.prog_group or user.math_group or user.ukr_group or user.english_group or user.opp_group))

    if is_configured:
        prog_disp = f"група {user.prog_group}" if user.prog_group else "Не обрано"
        math_disp = f"група {user.math_group}" if user.math_group else "Не обрано"
        ukr_disp = f"група {user.ukr_group}" if user.ukr_group else "Не обрано"
        eng_disp = user.english_group if user.english_group else "Не обрано"
        welcome_text = (
            f"👋 <b>Привіт, {message.from_user.first_name}!</b>\n\n"
            f"{week_status}\n\n"
            f"📌 <b>Ваші поточні налаштування:</b>\n"
            f"   ▫️ 💻 Мови програмування: <b>{prog_disp}</b>\n"
            f"   ▫️ 📐 Математика: <b>{math_disp}</b>\n"
            f"   ▫️ 🇺🇦 Українська мова: <b>{ukr_disp}</b>\n"
            f"   ▫️ 🇬🇧 Англійська мова: <b>{eng_disp}</b>\n"
            f"   ▫️ ⏰ Нагадування: <b>{user.notify_minutes} хв</b> до пари ({'🔔 увімкнено' if user.notifications_enabled else '🔕 вимкнено'})\n\n"
            f"Використовуйте кнопки меню нижче для перегляду розкладу або налаштувань. 👇"
        )
        await message.answer(
            welcome_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        # Початок 4-крокового вибору підгруп
        prog_groups = schedule_service.get_prog_groups()
        await state.set_state(RegistrationState.choosing_prog)

        intro_text = (
            f"👋 <b>Вітаю у боті розкладу та нагадувань!</b>\n\n"
            f"{week_status}\n\n"
            f"Для формування вашого точного розкладу та нагадувань оберіть підгрупи з 4 дисциплін:\n\n"
            f"👉 <b>Крок 1/4: Оберіть вашу підгрупу з Мов програмування (1–6):</b>"
        )
        await message.answer(
            intro_text,
            reply_markup=get_prog_groups_keyboard(prog_groups),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("select_prog:"))
async def on_prog_selected(callback: CallbackQuery, state: FSMContext):
    """Обробка вибору групи з програмування."""
    prog_group = callback.data.split(":", 1)[1]
    await update_user_prog_group(callback.from_user.id, prog_group)

    math_groups = schedule_service.get_math_groups()
    await state.set_state(RegistrationState.choosing_math)

    await callback.answer(f"Програмування: група {prog_group}")
    await callback.message.edit_text(
        f"✅ Мови програмування: <b>група {prog_group}</b>\n\n"
        f"👉 <b>Крок 2/4: Оберіть вашу підгрупу з Математики (1–3):</b>",
        reply_markup=get_math_groups_keyboard(math_groups),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("select_math:"))
async def on_math_selected(callback: CallbackQuery, state: FSMContext):
    """Обробка вибору групи з математики."""
    math_group = callback.data.split(":", 1)[1]
    await update_user_math_group(callback.from_user.id, math_group)

    ukr_groups = schedule_service.get_ukr_groups()
    await state.set_state(RegistrationState.choosing_ukr)

    await callback.answer(f"Математика: група {math_group}")
    await callback.message.edit_text(
        f"✅ Математика: <b>група {math_group}</b>\n\n"
        f"👉 <b>Крок 3/4: Оберіть вашу підгрупу з Української мови (5–8):</b>",
        reply_markup=get_ukr_groups_keyboard(ukr_groups),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("select_ukr:"))
async def on_ukr_selected(callback: CallbackQuery, state: FSMContext):
    """Обробка вибору групи з української мови."""
    ukr_group = callback.data.split(":", 1)[1]
    await update_user_ukr_group(callback.from_user.id, ukr_group)

    eng_groups = schedule_service.get_english_groups()
    await state.set_state(RegistrationState.choosing_english)

    await callback.answer(f"Українська мова: група {ukr_group}")
    await callback.message.edit_text(
        f"✅ Українська мова: <b>група {ukr_group}</b>\n\n"
        f"👉 <b>Крок 4/4: Оберіть вашу підгрупу з Англійської мови:</b>",
        reply_markup=get_english_groups_keyboard(eng_groups, show_skip=True),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("select_eng:"))
async def on_english_selected(callback: CallbackQuery, state: FSMContext):
    """Обробка вибору підгрупи з англійської мови."""
    eng_group = callback.data.split(":", 1)[1]
    if eng_group != "skip":
        await update_user_english_group(callback.from_user.id, eng_group)
        await callback.answer(f"Англійська: {eng_group}")
    else:
        await callback.answer("Англійську мову пропущено")
    await state.clear()

    user = await get_or_create_user(callback.from_user.id)
    eng_disp = user.english_group or "Не обрано"

    finish_text = (
        f"🎉 <b>Налаштування успішно завершено!</b>\n\n"
        f"📌 <b>Ваші обрані групи:</b>\n"
        f"   ▫️ 💻 Мови програмування: <b>група {user.prog_group or 'Не обрано'}</b>\n"
        f"   ▫️ 📐 Математика: <b>група {user.math_group or 'Не обрано'}</b>\n"
        f"   ▫️ 🇺🇦 Українська мова: <b>група {user.ukr_group or 'Не обрано'}</b>\n"
        f"   ▫️ 🇬🇧 Англійська мова: <b>{eng_disp}</b>\n\n"
        f"🔔 Нагадування: <b>за {user.notify_minutes} хв</b> до кожної пари.\n\n"
        f"Тепер ви можете зручно переглядати свій розклад через кнопки нижче. 👇"
    )

    await callback.message.edit_text(
        finish_text,
        parse_mode="HTML"
    )

    await callback.message.answer(
        "Оберіть дію в головному меню:",
        reply_markup=get_main_menu_keyboard()
    )
