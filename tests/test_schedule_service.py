from datetime import date
from bot.services.schedule_service import schedule_service


def test_opp_and_english_groups_loaded():
    schedule_service.reload()
    opp_groups = schedule_service.get_opp_groups()
    english_groups = schedule_service.get_english_groups()
    
    assert "КН-1" in opp_groups
    assert "КН-2" in opp_groups
    assert "КН-7" in opp_groups
    assert "A53" in english_groups
    assert "A67" in english_groups


def test_schedule_filtering_kn1_and_a53_monday():
    schedule_service.reload()
    # Понеділок (07.09.2026 — це понеділок 2-го тижня)
    target_date = date(2026, 9, 7)
    week_info, lessons = schedule_service.get_lessons_for_date(
        opp_group="КН-1",
        english_group="A53",
        target_date=target_date
    )
    
    assert week_info.week_number == 2
    subjects = [l.subject for l in lessons]
    
    # Очікується 07.09.2026 для КН-1 + A53:
    # 1. Англійська мова (A53)
    # 2. Дискретна математика (Лекція)
    # 3. Алгебра та геометрія (Лекція)
    # 4. Організація освітнього процесу (07.09.2026)
    assert "Англійська мова" in subjects
    assert "Дискретна математика" in subjects
    assert "Алгебра та геометрія" in subjects
    assert "Організація освітнього процесу" in subjects


def test_schedule_filtering_kn2_tuesday():
    schedule_service.reload()
    # Вівторок (08.09.2026 — це вівторок 2-го тижня)
    target_date = date(2026, 9, 8)
    week_info, lessons = schedule_service.get_lessons_for_date(
        opp_group="КН-2",
        english_group="A54",
        target_date=target_date
    )
    
    subjects = [l.subject for l in lessons]
    # Очікується 08.09.2026:
    # 1. Українська мова (Лекція)
    # 2. Алгебра та геометрія (Практика для КН-2)
    # 3. Мови програмування (Лекція)
    assert "Українська мова (за професійним спрямуванням)" in subjects
    assert "Алгебра та геометрія" in subjects
    assert "Мови програмування" in subjects


def test_format_day_schedule():
    schedule_service.reload()
    text = schedule_service.format_day_schedule(
        opp_group="КН-1",
        english_group="A53",
        target_date=date(2026, 9, 7)
    )
    assert "КН-1" in text
    assert "A53" in text
    assert "Англійська мова" in text
    assert "3-407" in text


def test_format_reminder_message():
    schedule_service.reload()
    _, lessons = schedule_service.get_lessons_for_date("КН-1", "A53", date(2026, 9, 7))
    first_lesson = lessons[0]
    reminder = schedule_service.format_reminder_message(first_lesson, minutes_left=10)
    
    assert "через 10 хв" in reminder
    assert first_lesson.subject in reminder
    assert first_lesson.teacher in reminder
    assert first_lesson.room in reminder




