import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union
from bot.config import config
from bot.services.week_service import UKRAINIAN_WEEKDAYS, WeekInfo, get_week_info

logger = logging.getLogger(__name__)


def parse_schedule_date(date_str: str, default_year: Optional[int] = None) -> Optional[date]:
    """
    Парсинг календарної дати з різних можливих форматів:
    - ISO: '2026-09-09'
    - Крапки: '9.09', '09.09', '09.09.2026', '01.09.25', '02.09.26', '11.09.26'
    - Скісні риски: '9/09', '09/09'
    """
    if default_year is None:
        default_year = config.SEMESTER_START_DATE.year

    s = date_str.strip()
    if not s:
        return None

    # Спроба стандартного ISO
    try:
        return date.fromisoformat(s)
    except ValueError:
        pass

    normalized = s.replace("/", ".").replace("-", ".")
    parts = normalized.split(".")
    if len(parts) == 2:
        try:
            day, month = int(parts[0]), int(parts[1])
            return date(default_year, month, day)
        except ValueError:
            return None
    elif len(parts) == 3:
        try:
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            if year < 100:
                year += 2000
            # Корекція року, якщо вказано помилково (наприклад 01.09.25)
            if year != default_year and month in (9, 10, 11, 12, 1):
                year = default_year
            return date(year, month, day)
        except ValueError:
            return None

    return None


@dataclass
class Lesson:
    id: str
    group: str
    subject: str
    type: str
    teacher: str
    room: str
    day_of_week: int
    category: str = "general"
    weeks: str = "all"  # наприклад "all", "2-14", "1-14", "2,4,6,8,10,12,14", "3,5,7,9,11,13", "14"
    specific_dates: List[str] = field(default_factory=list)  # наприклад ["2026-09-01", "2026-09-07"]
    start_time: str = "08:30"
    end_time: str = "09:50"

    @property
    def start_time_obj(self) -> time:
        hour, minute = map(int, self.start_time.split(":"))
        return time(hour, minute)

    @property
    def end_time_obj(self) -> time:
        hour, minute = map(int, self.end_time.split(":"))
        return time(hour, minute)

    @property
    def type_emoji(self) -> str:
        if self.category == "pe":
            return "🏃"
        t = self.type.lower()
        if "спорт" in t or "фіз" in t:
            return "🏃"
        elif "лекція" in t:
            return "📖"
        elif "практика" in t:
            return "✍️"
        elif "лабораторна" in t or "лаб" in t:
            return "🔬"
        elif "семінар" in t:
            return "💬"
        elif "зустріч" in t or "організація" in t or "вступна" in t:
            return "🏛️"
        elif "консультація" in t:
            return "💡"
        return "📚"

    def matches_week(self, week_number: int, week_type: int) -> bool:
        """Перевірка, чи відбувається заняття протягом вказаного тижня / парності."""
        # Якщо заняття прив'язане до конкретних дат, воно відображається ТІЛЬКИ на тому тижні, куди ці дати потрапляють
        if self.specific_dates:
            for d_str in self.specific_dates:
                d = parse_schedule_date(d_str)
                if d:
                    info = get_week_info(d)
                    if info.week_number == week_number:
                        return True
            return False

        w = self.weeks.strip().lower()
        if w == "specific":
            return False
        if w in ["all", "кожний", "всі", "*", ""]:
            return True
        if w in ["чисельник"]:
            return (week_number % 2 == 1) or (week_type == 1)
        if w in ["знаменник"]:
            return (week_number % 2 == 0) or (week_type == 2)

        # Підтримка довільних списків та діапазонів (наприклад "1, 3-14", "2-12", "2,4,6,8,10,12,14", "2", "14")
        allowed_weeks = set()
        has_conditions = False
        for part in w.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                subparts = part.split("-")
                if len(subparts) == 2 and subparts[0].strip().isdigit() and subparts[1].strip().isdigit():
                    s_w, e_w = int(subparts[0].strip()), int(subparts[1].strip())
                    allowed_weeks.update(range(s_w, e_w + 1))
                    has_conditions = True
            elif part.isdigit():
                allowed_weeks.add(int(part))
                has_conditions = True

        if has_conditions:
            return week_number in allowed_weeks

        return True

    def matches_date(self, target_date: date, week_number: int, week_type: int) -> bool:
        """Перевірка, чи відбувається заняття у цю конкретну календарну дату."""
        if self.specific_dates:
            for d_str in self.specific_dates:
                d = parse_schedule_date(d_str)
                if d and d == target_date:
                    return True
                target_str_iso = target_date.isoformat()
                target_str_uk = target_date.strftime("%d.%m.%Y")
                target_str_short = target_date.strftime("%d.%m.%y")
                target_str_day_month = target_date.strftime("%d.%m")
                target_str_alt = f"{target_date.day}.{target_date.month:02d}"

                d_clean = d_str.strip()
                if d_clean in (target_str_iso, target_str_uk, target_str_short, target_str_day_month, target_str_alt):
                    return True
            return False

        return self.matches_week(week_number, week_type)

    def matches_user_groups(
        self,
        prog_group: Optional[str] = None,
        math_group: Optional[str] = None,
        ukr_group: Optional[str] = None,
        english_group: Optional[str] = None,
        opp_group: Optional[str] = None,
        has_management: bool = False,
    ) -> bool:
        """Перевірка, чи стосується заняття обраних підгруп користувача."""
        if self.category == "management":
            return bool(has_management)

        if self.category == "pe":
            return True

        g = self.group.strip()
        if g in ["all", "Всі", "КН-all", "лекція", "Лекція", "*"]:
            return True

        # Дисциплінарні категорії
        if self.category == "programming":
            if prog_group and g == prog_group:
                return True
            if opp_group and opp_group.startswith("КН-") and g == opp_group.replace("КН-", ""):
                return True
            return False

        if self.category == "math":
            if math_group and g == math_group:
                return True
            if opp_group and opp_group.startswith("КН-") and g == opp_group.replace("КН-", ""):
                return True
            return False

        if self.category == "ukrainian":
            if ukr_group and g == ukr_group:
                return True
            if opp_group and opp_group.startswith("КН-") and g == opp_group.replace("КН-", ""):
                return True
            return False

        if self.category == "english":
            if not english_group:
                return False
            return g.replace("А", "A") == english_group.replace("А", "A")

        # Резервна перевірка
        if opp_group and (g == opp_group or g == opp_group.replace("КН-", "")):
            return True
        return False

    def matches_group(self, opp_group: str, english_group: str, has_management: bool = False) -> bool:
        """Метод для зворотної сумісності зі старими викликами."""
        num = opp_group.replace("КН-", "") if opp_group.startswith("КН-") else opp_group
        return self.matches_user_groups(
            prog_group=num,
            math_group=num,
            ukr_group=num,
            english_group=english_group,
            opp_group=opp_group,
            has_management=has_management,
        )


PAIR_TIME_MAP = {
    "08:30": "09:50",
    "10:00": "11:20",
    "11:40": "13:00",
    "13:30": "14:50",
    "15:00": "16:20",
    "16:30": "17:50",
    "18:00": "19:20",
}


def parse_pe_slots(pe_slots_raw: Union[None, str, List[dict]]) -> List[dict]:
    """Безпечний парсинг списку слотів фізичного виховання."""
    if not pe_slots_raw:
        return []
    if isinstance(pe_slots_raw, list):
        return pe_slots_raw
    if isinstance(pe_slots_raw, str):
        try:
            data = json.loads(pe_slots_raw)
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return []


def create_pe_lesson(day_of_week: int, start_time: str, end_time: Optional[str] = None) -> Lesson:
    """Генерація картки заняття з фізичного виховання."""
    end_t = end_time or PAIR_TIME_MAP.get(start_time, "09:50")
    return Lesson(
        id=f"pe_{day_of_week}_{start_time.replace(':', '')}",
        group="all",
        subject="Фізичне виховання",
        type="Практика",
        teacher="Кафедра фізичного виховання",
        room="Спорткомплекс",
        day_of_week=day_of_week,
        category="pe",
        weeks="all",
        start_time=start_time,
        end_time=end_t,
    )


class ScheduleService:
    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path or config.SCHEDULE_FILE_PATH
        self._last_mtime: float = 0.0
        self._prog_groups: List[str] = []
        self._math_groups: List[str] = []
        self._ukr_groups: List[str] = []
        self._english_groups: List[str] = []
        self._lessons: List[Lesson] = []
        self._check_and_reload()

    def _check_and_reload(self) -> None:
        """Автоматичне перезавантаження JSON даних, якщо файл змінено на диску."""
        try:
            if self.file_path.exists():
                mtime = self.file_path.stat().st_mtime
                if mtime != self._last_mtime:
                    self.reload()
                    self._last_mtime = mtime
        except Exception as e:
            logger.error(f"Error checking schedule file modification time: {e}")

    def reload(self) -> None:
        """Завантаження або перезавантаження розкладу з JSON файлу."""
        try:
            if not self.file_path.exists():
                logger.error(f"Schedule file not found at {self.file_path}")
                return

            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._prog_groups = data.get("prog_groups", ["1", "2", "3", "4", "5", "6"])
            self._math_groups = data.get("math_groups", ["1", "2", "3"])
            self._ukr_groups = data.get("ukr_groups", ["5", "6", "7", "8"])
            self._english_groups = data.get("english_groups", [])
            self._lessons = []

            for item in data.get("lessons", []):
                raw_weeks = str(item.get("weeks") or item.get("week_type") or "all").strip()
                raw_specific = item.get("specific_dates", [])
                if isinstance(raw_specific, str):
                    raw_specific = [raw_specific]
                specific_dates_val = list(raw_specific)

                # Перевіряємо, чи вказано в полі weeks конкретну календарну дату (наприклад "9.09", "11.09.26", "01.09.25")
                parsed_d = parse_schedule_date(raw_weeks)
                if parsed_d is not None and not (raw_weeks.isdigit() or ("-" in raw_weeks and not any(c in raw_weeks for c in [".", "/"]))):
                    iso_str = parsed_d.isoformat()
                    if iso_str not in specific_dates_val:
                        specific_dates_val.append(iso_str)
                    weeks_val = "specific"
                else:
                    weeks_val = raw_weeks

                lesson = Lesson(
                    id=item.get("id", f"{item.get('group')}_{item.get('day_of_week')}_{item.get('start_time')}"),
                    group=item["group"],
                    subject=item["subject"],
                    type=item.get("type", "Заняття"),
                    teacher=item.get("teacher", "Не вказано"),
                    room=item.get("room", "Не вказано"),
                    day_of_week=int(item["day_of_week"]),
                    category=item.get("category", "general"),
                    weeks=weeks_val,
                    specific_dates=specific_dates_val,
                    start_time=item["start_time"],
                    end_time=item["end_time"],
                )
                self._lessons.append(lesson)

            if self.file_path.exists():
                self._last_mtime = self.file_path.stat().st_mtime

            logger.info(f"Loaded {len(self._lessons)} lessons from {self.file_path}")
        except Exception as e:
            logger.exception(f"Error loading schedule JSON: {e}")

    def get_prog_groups(self) -> List[str]:
        self._check_and_reload()
        return self._prog_groups

    def get_math_groups(self) -> List[str]:
        self._check_and_reload()
        return self._math_groups

    def get_ukr_groups(self) -> List[str]:
        self._check_and_reload()
        return self._ukr_groups

    def get_english_groups(self) -> List[str]:
        self._check_and_reload()
        return self._english_groups

    def get_opp_groups(self) -> List[str]:
        """Для зворотної сумісності."""
        self._check_and_reload()
        return [f"КН-{g}" for g in self._prog_groups]

    @staticmethod
    def format_groups_header(
        prog_group: Optional[str] = None,
        math_group: Optional[str] = None,
        ukr_group: Optional[str] = None,
        english_group: Optional[str] = None,
        opp_group: Optional[str] = None,
        has_management: bool = False,
        pe_slots: Optional[Union[str, List[dict]]] = None,
    ) -> str:
        """Форматування охайного рядка обраних груп."""
        parts = []
        if prog_group:
            parts.append(f"💻 Пр-{prog_group}")
        if math_group:
            parts.append(f"📐 Мат-{math_group}")
        if ukr_group:
            parts.append(f"🇺🇦 Укр-{ukr_group}")
        if english_group:
            parts.append(f"🇬🇧 {english_group}")
        if not parts and opp_group:
            parts.append(f"👥 {opp_group}")
        if has_management:
            parts.append("📊 Менеджмент")
        pe_list = parse_pe_slots(pe_slots)
        if pe_list:
            parts.append(f"🏃 Фізвиховання ({len(pe_list)} пар)")
        return " | ".join(parts) if parts else "Не обрано"

    def get_lessons_for_day_and_week(
        self,
        prog_group: Optional[str] = None,
        math_group: Optional[str] = None,
        ukr_group: Optional[str] = None,
        english_group: Optional[str] = None,
        day_of_week: int = 0,
        week_number: int = 1,
        week_type: int = 1,
        opp_group: Optional[str] = None,
        has_management: bool = False,
        pe_slots: Optional[Union[str, List[dict]]] = None,
    ) -> List[Lesson]:
        """Фільтрація занять для конкретного дня та номера/парності тижня."""
        self._check_and_reload()
        matched: List[Lesson] = []

        for lesson in self._lessons:
            if not lesson.matches_user_groups(
                prog_group=prog_group,
                math_group=math_group,
                ukr_group=ukr_group,
                english_group=english_group,
                opp_group=opp_group,
                has_management=has_management,
            ):
                continue
            if lesson.day_of_week != day_of_week:
                continue
            if lesson.matches_week(week_number, week_type):
                matched.append(lesson)

        # Інжекція слотів фізичного виховання
        for slot in parse_pe_slots(pe_slots):
            if int(slot.get("day_of_week", -1)) == day_of_week:
                st = slot.get("start_time", "08:30")
                et = slot.get("end_time") or PAIR_TIME_MAP.get(st, "09:50")
                matched.append(create_pe_lesson(day_of_week, st, et))

        matched.sort(key=lambda l: l.start_time)
        return matched

    def get_lessons_for_date(
        self,
        prog_group: Optional[str] = None,
        math_group: Optional[str] = None,
        ukr_group: Optional[str] = None,
        english_group: Optional[str] = None,
        target_date: Optional[date] = None,
        opp_group: Optional[str] = None,
        has_management: bool = False,
        pe_slots: Optional[Union[str, List[dict]]] = None,
    ) -> Tuple[WeekInfo, List[Lesson]]:
        """Отримання занять для конкретної календарної дати."""
        self._check_and_reload()
        if target_date is None:
            target_date = datetime.now(config.timezone).date()

        week_info = get_week_info(target_date)
        day_of_week = target_date.weekday()

        matched: List[Lesson] = []
        for lesson in self._lessons:
            if not lesson.matches_user_groups(
                prog_group=prog_group,
                math_group=math_group,
                ukr_group=ukr_group,
                english_group=english_group,
                opp_group=opp_group,
                has_management=has_management,
            ):
                continue
            if lesson.day_of_week != day_of_week:
                continue
            if lesson.matches_date(target_date, week_info.week_number, week_info.week_type):
                matched.append(lesson)

        # Інжекція слотів фізичного виховання
        for slot in parse_pe_slots(pe_slots):
            if int(slot.get("day_of_week", -1)) == day_of_week:
                st = slot.get("start_time", "08:30")
                et = slot.get("end_time") or PAIR_TIME_MAP.get(st, "09:50")
                matched.append(create_pe_lesson(day_of_week, st, et))

        matched.sort(key=lambda l: l.start_time)
        return week_info, matched

    def format_single_lesson(self, lesson: Lesson, index: Optional[int] = None) -> str:
        """Форматування картки одного заняття."""
        num_str = f"<b>{index}.</b> " if index is not None else ""
        if lesson.specific_dates:
            dates_formatted = []
            for d_str in lesson.specific_dates:
                d = parse_schedule_date(d_str)
                dates_formatted.append(d.strftime("%d.%m.%Y") if d else d_str)
            weeks_info = f" (разово: {', '.join(dates_formatted)})"
        elif lesson.weeks != "all":
            weeks_info = f" (тижні: {lesson.weeks})"
        else:
            weeks_info = ""
        group_display = f"гр. {lesson.group}" if lesson.group != "all" else "Всі"
        return (
            f"{num_str}<b>{lesson.start_time} - {lesson.end_time}</b> | {lesson.type_emoji} <b>{lesson.subject}</b>\n"
            f"   ▫️ <i>Тип:</i> {lesson.type}{weeks_info}\n"
            f"   ▫️ <i>Викладач:</i> {lesson.teacher}\n"
            f"   ▫️ <i>Аудиторія / Лінк:</i> <b>{lesson.room}</b>\n"
            f"   ▫️ <i>Група:</i> {group_display}"
        )

    def format_day_schedule(
        self,
        prog_group: Optional[str] = None,
        math_group: Optional[str] = None,
        ukr_group: Optional[str] = None,
        english_group: Optional[str] = None,
        target_date: Optional[date] = None,
        title_prefix: str = "Розклад",
        opp_group: Optional[str] = None,
        has_management: bool = False,
        pe_slots: Optional[Union[str, List[dict]]] = None,
    ) -> str:
        """Форматування повного тексту розкладу на день."""
        self._check_and_reload()
        if target_date is None:
            target_date = datetime.now(config.timezone).date()

        week_info, lessons = self.get_lessons_for_date(
            prog_group=prog_group,
            math_group=math_group,
            ukr_group=ukr_group,
            english_group=english_group,
            target_date=target_date,
            opp_group=opp_group,
            has_management=has_management,
            pe_slots=pe_slots,
        )
        date_str = target_date.strftime("%d.%m.%Y")
        groups_line = self.format_groups_header(
            prog_group=prog_group,
            math_group=math_group,
            ukr_group=ukr_group,
            english_group=english_group,
            opp_group=opp_group,
            has_management=has_management,
            pe_slots=pe_slots,
        )

        header = (
            f"📋 <b>{title_prefix} на {week_info.day_name_uk} ({date_str})</b>\n"
            f"👥 {groups_line}\n"
            f"🔹 Тиждень: <b>{week_info.week_number}-й ({week_info.week_type_name})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━"
        )

        if not lessons:
            return f"{header}\n\n🎉 <b>Занять немає! Можна відпочивати або зайнятися своїми справами.</b>"

        lessons_text = "\n\n".join(
            self.format_single_lesson(lesson, i + 1) for i, lesson in enumerate(lessons)
        )
        return f"{header}\n\n{lessons_text}"

    def format_week_schedule(
        self,
        prog_group: Optional[str] = None,
        math_group: Optional[str] = None,
        ukr_group: Optional[str] = None,
        english_group: Optional[str] = None,
        target_date: Optional[date] = None,
        week_number_override: Optional[int] = None,
        opp_group: Optional[str] = None,
        has_management: bool = False,
        pe_slots: Optional[Union[str, List[dict]]] = None,
    ) -> str:
        """Форматування розкладу на всі 6 робочих днів конкретного навчального тижня."""
        self._check_and_reload()
        if target_date is None:
            now = datetime.now(config.timezone)
            target_date = now.date()

        current_week_info = get_week_info(target_date)
        week_num = week_number_override if week_number_override is not None else current_week_info.week_number
        week_type = 1 if (week_num % 2 == 1) else 2
        type_title = "Непарний (1-й тиждень)" if week_type == 1 else "Парний (2-й тиждень)"
        current_mark = " (поточний)" if week_num == current_week_info.week_number else ""
        groups_line = self.format_groups_header(
            prog_group=prog_group,
            math_group=math_group,
            ukr_group=ukr_group,
            english_group=english_group,
            opp_group=opp_group,
            has_management=has_management,
            pe_slots=pe_slots,
        )

        header = (
            f"📆 <b>Розклад на {week_num}-й тиждень{current_mark}</b>\n"
            f"🔹 Тип тижня: <b>{type_title}</b>\n"
            f"👥 {groups_line}\n"
            f"━━━━━━━━━━━━━━━━━━━━━"
        )

        days_output = []
        for day_idx in range(6):  # Від понеділка до суботи (від 0 до 5)
            day_lessons = self.get_lessons_for_day_and_week(
                prog_group=prog_group,
                math_group=math_group,
                ukr_group=ukr_group,
                english_group=english_group,
                day_of_week=day_idx,
                week_number=week_num,
                week_type=week_type,
                opp_group=opp_group,
                has_management=has_management,
                pe_slots=pe_slots,
            )
            day_name = UKRAINIAN_WEEKDAYS[day_idx]

            if not day_lessons:
                days_output.append(f"📌 <b>{day_name}</b>: <i>Занять немає</i>")
            else:
                formatted_lessons = []
                for lesson in day_lessons:
                    extra = ""
                    if lesson.specific_dates:
                        d_obj = parse_schedule_date(lesson.specific_dates[0])
                        date_label = d_obj.strftime("%d.%m") if d_obj else lesson.specific_dates[0]
                        extra = f", 🗓️ разово {date_label}"
                    formatted_lessons.append(
                        f"  {lesson.type_emoji} <code>{lesson.start_time}-{lesson.end_time}</code> {lesson.subject} (<i>{lesson.type}{extra}, <b>{lesson.room}</b></i>)"
                    )
                days_output.append(f"📌 <b>{day_name}</b>:\n" + "\n".join(formatted_lessons))

        return f"{header}\n\n" + "\n\n".join(days_output)

    def get_current_and_next_lesson(
        self,
        prog_group: Optional[str] = None,
        math_group: Optional[str] = None,
        ukr_group: Optional[str] = None,
        english_group: Optional[str] = None,
        current_dt: Optional[datetime] = None,
        opp_group: Optional[str] = None,
        has_management: bool = False,
        pe_slots: Optional[Union[str, List[dict]]] = None,
    ) -> Tuple[Optional[Lesson], Optional[Lesson]]:
        """Пошук (поточного заняття, наступного заняття) на цей момент."""
        if current_dt is None:
            current_dt = datetime.now(config.timezone)

        current_date = current_dt.date()
        current_time = current_dt.time()

        _, lessons = self.get_lessons_for_date(
            prog_group=prog_group,
            math_group=math_group,
            ukr_group=ukr_group,
            english_group=english_group,
            target_date=current_date,
            opp_group=opp_group,
            has_management=has_management,
            pe_slots=pe_slots,
        )
        if not lessons:
            return None, None

        current_lesson = None
        next_lesson = None

        for lesson in lessons:
            start = lesson.start_time_obj
            end = lesson.end_time_obj
            if start <= current_time <= end:
                current_lesson = lesson
            elif current_time < start:
                if next_lesson is None or lesson.start_time_obj < next_lesson.start_time_obj:
                    next_lesson = lesson

        return current_lesson, next_lesson

    def format_now_schedule(
        self,
        prog_group: Optional[str] = None,
        math_group: Optional[str] = None,
        ukr_group: Optional[str] = None,
        english_group: Optional[str] = None,
        current_dt: Optional[datetime] = None,
        opp_group: Optional[str] = None,
        has_management: bool = False,
        pe_slots: Optional[Union[str, List[dict]]] = None,
    ) -> str:
        """Форматування повідомлення статусу щодо того, що відбувається прямо зараз."""
        if current_dt is None:
            current_dt = datetime.now(config.timezone)

        week_info = get_week_info(current_dt.date())
        time_str = current_dt.strftime("%H:%M")
        current_lesson, next_lesson = self.get_current_and_next_lesson(
            prog_group=prog_group,
            math_group=math_group,
            ukr_group=ukr_group,
            english_group=english_group,
            current_dt=current_dt,
            opp_group=opp_group,
            has_management=has_management,
            pe_slots=pe_slots,
        )
        groups_line = self.format_groups_header(
            prog_group=prog_group,
            math_group=math_group,
            ukr_group=ukr_group,
            english_group=english_group,
            opp_group=opp_group,
            has_management=has_management,
            pe_slots=pe_slots,
        )

        header = (
            f"⏳ <b>Поточний стан ({time_str})</b>\n"
            f"📅 <b>{week_info.day_name_uk}</b> | {week_info.week_type_name}\n"
            f"👥 {groups_line}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        content = []
        if current_lesson:
            content.append(f"🟢 <b>Зараз триває пара:</b>\n{self.format_single_lesson(current_lesson)}")
        else:
            content.append("⚪ <b>Зараз пари немає.</b>")

        if next_lesson:
            content.append(f"🔜 <b>Наступна пара:</b>\n{self.format_single_lesson(next_lesson)}")
        else:
            if not current_lesson:
                content.append("🏁 <i>На сьогодні більше занять не заплановано.</i>")

        return header + "\n\n".join(content)

    def format_reminder_message(self, lesson: Lesson, minutes_left: int) -> str:
        """Форматування тексту сповіщення перед початком пари."""
        time_text = "зараз" if minutes_left <= 0 else f"через {minutes_left} хв"
        group_display = f"гр. {lesson.group}" if lesson.group != "all" else "Всі"
        return (
            f"🔔 <b>Нагадування про пару ({time_text})!</b>\n\n"
            f"{lesson.type_emoji} <b>{lesson.subject}</b> (<i>{lesson.type}</i>)\n"
            f"⏰ <b>Час:</b> <code>{lesson.start_time} - {lesson.end_time}</code>\n"
            f"👨‍🏫 <b>Викладач:</b> {lesson.teacher}\n"
            f"🚪 <b>Аудиторія / Посилання:</b> <b>{lesson.room}</b>\n"
            f"👥 <b>Група:</b> {group_display}"
        )


schedule_service = ScheduleService()
