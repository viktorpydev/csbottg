from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional
from bot.config import config


@dataclass
class WeekInfo:
    target_date: date
    week_number: int  # 1, 2, 3, ...
    week_type: int  # 1 (Непарний) або 2 (Парний)
    week_type_name: str  # "Непарний тиждень" або "Парний тиждень"
    is_before_semester: bool
    days_until_semester: int
    day_name_uk: str


UKRAINIAN_WEEKDAYS = [
    "Понеділок",
    "Вівторок",
    "Середа",
    "Четвер",
    "П'ятниця",
    "Субота",
    "Неділя"
]


def get_current_date() -> date:
    """Отримання поточної дати у налаштованому часовому поясі."""
    now = datetime.now(config.timezone)
    return now.date()


def get_week_info(target_date: Optional[date] = None) -> WeekInfo:
    """
    Розрахунок номера та типу навчального тижня (непарний/парний)
    для заданої дати на основі SEMESTER_START_DATE (01.09.2026).
    
    Перший навчальний тиждень починається з понеділка, що містить SEMESTER_START_DATE.
    """
    if target_date is None:
        target_date = get_current_date()

    semester_start = config.SEMESTER_START_DATE
    # Понеділок тижня, що містить дату початку семестру
    semester_start_monday = semester_start - timedelta(days=semester_start.weekday())

    diff_days = (target_date - semester_start_monday).days

    if diff_days < 0:
        days_until = (semester_start - target_date).days
        # Для попереднього перегляду до початку семестру вважаємо майбутній тиждень 1-м тижнем
        week_num = 1
        week_type = 1
        week_type_name = "Непарний (1-й тиждень)"
        is_before = True
    else:
        week_num = (diff_days // 7) + 1
        week_type = 1 if (week_num % 2 == 1) else 2
        week_type_name = "Непарний (1-й тиждень)" if week_type == 1 else "Парний (2-й тиждень)"
        is_before = False
        days_until = 0

    day_name = UKRAINIAN_WEEKDAYS[target_date.weekday()]

    return WeekInfo(
        target_date=target_date,
        week_number=week_num,
        week_type=week_type,
        week_type_name=week_type_name,
        is_before_semester=is_before,
        days_until_semester=days_until,
        day_name_uk=day_name
    )


def format_week_header(target_date: Optional[date] = None) -> str:
    """Форматування зрозумілого рядочка зі статусом тижня."""
    info = get_week_info(target_date)
    formatted_date = info.target_date.strftime("%d.%m.%Y")
    
    if info.is_before_semester:
        return (
            f"📅 <b>{info.day_name_uk}, {formatted_date}</b>\n"
            f"⏳ <i>До початку семестру (01.09.2026) залишилось: {info.days_until_semester} дн.</i>\n"
            f"📌 <i>Початок з 1-го тижня ({info.week_type_name})</i>"
        )
    
    return (
        f"📅 <b>{info.day_name_uk}, {formatted_date}</b>\n"
        f"🔹 <b>{info.week_number}-й навчальний тиждень</b> — {info.week_type_name}"
    )
