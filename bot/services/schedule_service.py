import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union
from bot.config import config
from bot.services.week_service import UKRAINIAN_WEEKDAYS, WeekInfo, get_week_info

logger = logging.getLogger(__name__)


@dataclass
class Lesson:
    id: str
    group: str
    subject: str
    type: str
    teacher: str
    room: str
    day_of_week: int
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
        t = self.type.lower()
        if "лекція" in t:
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
        w = self.weeks.strip().lower()
        if w in ["all", "кожний", "всі", "*", ""]:
            return True
        if w in ["1", "чисельник"]:
            return (week_number % 2 == 1) or (week_type == 1)
        if w in ["2", "знаменник"]:
            return (week_number % 2 == 0) or (week_type == 2)
        
        # Діапазон, наприклад "2-14"
        if "-" in w:
            try:
                start_w, end_w = map(int, w.split("-"))
                return start_w <= week_number <= end_w
            except ValueError:
                pass

        # Перелік через кому, наприклад "2,4,6,8,10,12,14" або поодинокий "14"
        try:
            allowed_weeks = [int(item.strip()) for item in w.split(",") if item.strip().isdigit()]
            if allowed_weeks:
                return week_number in allowed_weeks
        except ValueError:
            pass

        return True

    def matches_date(self, target_date: date, week_number: int, week_type: int) -> bool:
        """Перевірка, чи відбувається заняття у цю конкретну календарну дату."""
        if self.specific_dates:
            target_str_iso = target_date.isoformat()
            target_str_uk = target_date.strftime("%d.%m.%Y")
            target_str_short = target_date.strftime("%d.%m.%y")
            target_str_day_month = target_date.strftime("%d.%m")
            target_str_alt = f"{target_date.day}.{target_date.month:02d}"

            for d in self.specific_dates:
                d_clean = d.strip()
                if d_clean in (target_str_iso, target_str_uk, target_str_short, target_str_day_month, target_str_alt):
                    return True
            return False

        return self.matches_week(week_number, week_type)

    def matches_group(self, opp_group: str, english_group: str) -> bool:
        """Перевірка, чи стосується заняття групи ОПП або англійської підгрупи користувача."""
        g = self.group.strip()
        if g in ["all", "Всі", "КН-all", "лекція", "Лекція", "*"]:
            return True
        if g == opp_group or g == english_group:
            return True
        # Також перевірка, якщо група "1", а користувач з "КН-1" тощо.
        if opp_group.startswith("КН-") and g == opp_group.replace("КН-", ""):
            return True
        return False


class ScheduleService:
    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path or config.SCHEDULE_FILE_PATH
        self._last_mtime: float = 0.0
        self._opp_groups: List[str] = []
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

            self._opp_groups = data.get("opp_groups", [])
            self._english_groups = data.get("english_groups", [])
            self._lessons = []

            for item in data.get("lessons", []):
                weeks_val = str(item.get("weeks") or item.get("week_type") or "all")
                specific_dates_val = item.get("specific_dates", [])
                if isinstance(specific_dates_val, str):
                    specific_dates_val = [specific_dates_val]

                lesson = Lesson(
                    id=item.get("id", f"{item.get('group')}_{item.get('day_of_week')}_{item.get('start_time')}"),
                    group=item["group"],
                    subject=item["subject"],
                    type=item.get("type", "Заняття"),
                    teacher=item.get("teacher", "Не вказано"),
                    room=item.get("room", "Не вказано"),
                    day_of_week=int(item["day_of_week"]),
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

    def get_opp_groups(self) -> List[str]:
        self._check_and_reload()
        return self._opp_groups

    def get_english_groups(self) -> List[str]:
        self._check_and_reload()
        return self._english_groups

    def get_lessons_for_day_and_week(
        self,
        opp_group: str,
        english_group: str,
        day_of_week: int,
        week_number: int,
        week_type: int
    ) -> List[Lesson]:
        """Фільтрація занять для конкретного дня та номера/парності тижня."""
        self._check_and_reload()
        matched: List[Lesson] = []

        for lesson in self._lessons:
            if not lesson.matches_group(opp_group, english_group):
                continue
            if lesson.day_of_week != day_of_week:
                continue
            if lesson.matches_week(week_number, week_type):
                matched.append(lesson)

        matched.sort(key=lambda l: l.start_time)
        return matched

    def get_lessons_for_date(
        self,
        opp_group: str,
        english_group: str,
        target_date: date
    ) -> Tuple[WeekInfo, List[Lesson]]:
        """Отримання занять для конкретної календарної дати."""
        self._check_and_reload()
        week_info = get_week_info(target_date)
        day_of_week = target_date.weekday()
        
        matched: List[Lesson] = []
        for lesson in self._lessons:
            if not lesson.matches_group(opp_group, english_group):
                continue
            if lesson.day_of_week != day_of_week:
                continue
            if lesson.matches_date(target_date, week_info.week_number, week_info.week_type):
                matched.append(lesson)

        matched.sort(key=lambda l: l.start_time)
        return week_info, matched

    def format_single_lesson(self, lesson: Lesson, index: Optional[int] = None) -> str:
        """Форматування картки одного заняття."""
        num_str = f"<b>{index}.</b> " if index is not None else ""
        weeks_info = f" (тижні: {lesson.weeks})" if lesson.weeks != "all" else ""
        return (
            f"{num_str}<b>{lesson.start_time} - {lesson.end_time}</b> | {lesson.type_emoji} <b>{lesson.subject}</b>\n"
            f"   ▫️ <i>Тип:</i> {lesson.type}{weeks_info}\n"
            f"   ▫️ <i>Викладач:</i> {lesson.teacher}\n"
            f"   ▫️ <i>Аудиторія / Лінк:</i> <b>{lesson.room}</b>\n"
            f"   ▫️ <i>Група:</i> {lesson.group}"
        )

    def format_day_schedule(
        self,
        opp_group: str,
        english_group: str,
        target_date: date,
        title_prefix: str = "Розклад"
    ) -> str:
        """Форматування повного тексту розкладу на день."""
        self._check_and_reload()
        week_info, lessons = self.get_lessons_for_date(opp_group, english_group, target_date)
        date_str = target_date.strftime("%d.%m.%Y")
        
        header = (
            f"📋 <b>{title_prefix} на {week_info.day_name_uk} ({date_str})</b>\n"
            f"👥 Групи: <b>{opp_group}</b> | <b>{english_group}</b>\n"
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
        opp_group: str,
        english_group: str,
        target_date: Optional[date] = None,
        week_number_override: Optional[int] = None
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

        header = (
            f"📆 <b>Розклад на {week_num}-й тиждень{current_mark}</b>\n"
            f"🔹 Тип тижня: <b>{type_title}</b>\n"
            f"👥 Групи: <b>{opp_group}</b> | <b>{english_group}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━"
        )

        days_output = []
        for day_idx in range(6):  # Від понеділка до суботи (від 0 до 5)
            day_lessons = self.get_lessons_for_day_and_week(
                opp_group,
                english_group,
                day_idx,
                week_num,
                week_type
            )
            day_name = UKRAINIAN_WEEKDAYS[day_idx]
            
            if not day_lessons:
                days_output.append(f"📌 <b>{day_name}</b>: <i>Занять немає</i>")
            else:
                formatted_lessons = "\n".join(
                    f"  {lesson.type_emoji} <code>{lesson.start_time}-{lesson.end_time}</code> {lesson.subject} (<i>{lesson.type}, <b>{lesson.room}</b></i>)"
                    for lesson in day_lessons
                )
                days_output.append(f"📌 <b>{day_name}</b>:\n{formatted_lessons}")

        return f"{header}\n\n" + "\n\n".join(days_output)

    def get_current_and_next_lesson(
        self,
        opp_group: str,
        english_group: str,
        current_dt: Optional[datetime] = None
    ) -> Tuple[Optional[Lesson], Optional[Lesson]]:
        """Пошук (поточного заняття, наступного заняття) на цей момент."""
        if current_dt is None:
            current_dt = datetime.now(config.timezone)

        current_date = current_dt.date()
        current_time = current_dt.time()
        
        _, lessons = self.get_lessons_for_date(opp_group, english_group, current_date)
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
        opp_group: str,
        english_group: str,
        current_dt: Optional[datetime] = None
    ) -> str:
        """Форматування повідомлення статусу щодо того, що відбувається прямо зараз."""
        if current_dt is None:
            current_dt = datetime.now(config.timezone)

        week_info = get_week_info(current_dt.date())
        time_str = current_dt.strftime("%H:%M")
        current_lesson, next_lesson = self.get_current_and_next_lesson(opp_group, english_group, current_dt)

        header = (
            f"⏳ <b>Поточний стан ({time_str})</b>\n"
            f"📅 <b>{week_info.day_name_uk}</b> | {week_info.week_type_name}\n"
            f"👥 Групи: <b>{opp_group}</b> | <b>{english_group}</b>\n"
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
        return (
            f"🔔 <b>Нагадування про пару ({time_text})!</b>\n\n"
            f"{lesson.type_emoji} <b>{lesson.subject}</b> (<i>{lesson.type}</i>)\n"
            f"⏰ <b>Час:</b> <code>{lesson.start_time} - {lesson.end_time}</code>\n"
            f"👨‍🏫 <b>Викладач:</b> {lesson.teacher}\n"
            f"🚪 <b>Аудиторія / Посилання:</b> <b>{lesson.room}</b>\n"
            f"👥 <b>Група:</b> {lesson.group}"
        )


schedule_service = ScheduleService()
