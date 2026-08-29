from datetime import date
from bot.services.week_service import get_week_info


def test_first_week_semester_start():
    # 01.09.2026 — це вівторок 1-го тижня
    d = date(2026, 9, 1)
    info = get_week_info(d)
    assert info.week_number == 1
    assert info.week_type == 1
    assert "Непарний" in info.week_type_name
    assert not info.is_before_semester
    assert info.day_name_uk == "Вівторок"


def test_first_week_sunday():
    # 06.09.2026 — це неділя 1-го тижня
    d = date(2026, 9, 6)
    info = get_week_info(d)
    assert info.week_number == 1
    assert info.week_type == 1
    assert info.day_name_uk == "Неділя"


def test_second_week_monday():
    # 07.09.2026 — це понеділок 2-го тижня (Парний)
    d = date(2026, 9, 7)
    info = get_week_info(d)
    assert info.week_number == 2
    assert info.week_type == 2
    assert "Парний" in info.week_type_name
    assert info.day_name_uk == "Понеділок"


def test_third_week_monday():
    # 14.09.2026 — це понеділок 3-го тижня (Непарний)
    d = date(2026, 9, 14)
    info = get_week_info(d)
    assert info.week_number == 3
    assert info.week_type == 1
    assert "Непарний" in info.week_type_name


def test_date_before_semester():
    # 26.08.2026 — це до початку семестру
    d = date(2026, 8, 26)
    info = get_week_info(d)
    assert info.is_before_semester
    assert info.days_until_semester == 6
