from datetime import date
from bot.services.schedule_service import schedule_service


def test_groups_loaded():
    schedule_service.reload()
    prog_groups = schedule_service.get_prog_groups()
    math_groups = schedule_service.get_math_groups()
    ukr_groups = schedule_service.get_ukr_groups()
    english_groups = schedule_service.get_english_groups()

    assert prog_groups == ["1", "2", "3", "4", "5", "6"]
    assert math_groups == ["1", "2", "3"]
    assert ukr_groups == ["5", "6", "7", "8"]
    assert "A51" in english_groups
    assert "A65" in english_groups


def test_schedule_filtering_monday_week_2():
    schedule_service.reload()
    # Понеділок 2-го тижня (07.09.2026)
    target_date = date(2026, 9, 7)
    week_info, lessons = schedule_service.get_lessons_for_date(
        prog_group="1",
        math_group="1",
        ukr_group="8",
        english_group="A53",
        target_date=target_date
    )

    assert week_info.week_number == 2
    subjects = [l.subject for l in lessons]

    assert "Англійська мова" in subjects
    assert "Дискретна математика" in subjects
    assert "Алгебра та геометрія" in subjects
    assert "Організація освітнього процесу" in subjects


def test_schedule_filtering_monday_week_6_with_ukr_group_8():
    schedule_service.reload()
    # Понеділок 6-го тижня (05.10.2026) - заняття з укр. мови (тижні 6-13)
    target_date = date(2026, 10, 5)
    week_info, lessons = schedule_service.get_lessons_for_date(
        prog_group="1",
        math_group="1",
        ukr_group="8",
        english_group="A53",
        target_date=target_date
    )

    assert week_info.week_number == 6
    subjects = [l.subject for l in lessons]

    assert "Англійська мова" in subjects
    assert "Українська мова (за професійним спрямуванням)" in subjects
    assert "Дискретна математика" in subjects
    assert "Алгебра та геометрія" in subjects

    ukr_lesson = next(l for l in lessons if l.subject == "Українська мова (за професійним спрямуванням)")
    assert ukr_lesson.group == "8"


def test_schedule_filtering_tuesday_math_group_2():
    schedule_service.reload()
    # Вівторок 2-го тижня (08.09.2026)
    target_date = date(2026, 9, 8)
    week_info, lessons = schedule_service.get_lessons_for_date(
        prog_group="2",
        math_group="2",
        ukr_group="6",
        english_group="A54",
        target_date=target_date
    )

    subjects = [l.subject for l in lessons]
    assert "Українська мова (за професійним спрямуванням)" in subjects
    assert "Алгебра та геометрія" in subjects
    assert "Мови програмування" in subjects

    math_lesson = next(l for l in lessons if l.subject == "Алгебра та геометрія")
    assert math_lesson.group == "2"


def test_schedule_filtering_thursday_week_6_prog_group_2_ukr_5():
    schedule_service.reload()
    # Четвер 6-го тижня (08.10.2026)
    target_date = date(2026, 10, 8)
    week_info, lessons = schedule_service.get_lessons_for_date(
        prog_group="2",
        math_group="1",
        ukr_group="5",
        english_group="A53",
        target_date=target_date
    )

    subjects = [l.subject for l in lessons]
    assert "Українська мова (за професійним спрямуванням)" in subjects
    assert "Мови програмування" in subjects

    prog_lesson = next(l for l in lessons if l.subject == "Мови програмування")
    assert prog_lesson.group == "2"
    assert prog_lesson.type == "Лабораторна"

    ukr_lesson = next(l for l in lessons if l.subject == "Українська мова (за професійним спрямуванням)")
    assert ukr_lesson.group == "5"


def test_format_day_schedule():
    schedule_service.reload()
    text = schedule_service.format_day_schedule(
        prog_group="1",
        math_group="1",
        ukr_group="8",
        english_group="A51",
        target_date=date(2026, 9, 7)
    )
    assert "Пр-1" in text
    assert "Мат-1" in text
    assert "Укр-8" in text
    assert "A51" in text
    assert "Англійська мова" in text
    assert "3-407" in text


def test_format_reminder_message():
    schedule_service.reload()
    _, lessons = schedule_service.get_lessons_for_date(
        prog_group="1",
        math_group="1",
        ukr_group="8",
        english_group="A53",
        target_date=date(2026, 9, 7)
    )
    first_lesson = lessons[0]
    reminder = schedule_service.format_reminder_message(first_lesson, minutes_left=10)

    assert "через 10 хв" in reminder
    assert first_lesson.subject in reminder
    assert first_lesson.teacher in reminder
    assert first_lesson.room in reminder


def test_one_off_events_and_national_defense():
    schedule_service.reload()
    # 01.09.2026: Вступна лекція Президента та Азаров
    _, lessons_sep1 = schedule_service.get_lessons_for_date(
        prog_group="3",
        math_group="2",
        ukr_group="7",
        english_group="A60",
        target_date=date(2026, 9, 1)
    )
    subjects_sep1 = [l.subject for l in lessons_sep1]
    assert "Вступна лекція Президента НаУКМА" in subjects_sep1
    assert "Відтепер спудеї/ки: що таке університет?" in subjects_sep1

    # Четвер на 5-му тижні (01.10.2026) - Основи національного супротиву (лекції)
    _, lessons_thu = schedule_service.get_lessons_for_date(
        prog_group="5",
        math_group="3",
        ukr_group="6",
        english_group="A58",
        target_date=date(2026, 10, 1)
    )
    subjects_thu = [l.subject for l in lessons_thu]
    assert "Основи національного супротиву" in subjects_thu


def test_one_off_events_in_week_view():
    schedule_service.reload()
    # Середа 1-го тижня (02.09.2026)
    wed_w1 = schedule_service.get_lessons_for_day_and_week(
        prog_group="1",
        math_group="1",
        ukr_group="5",
        english_group="A53",
        day_of_week=2,
        week_number=1,
        week_type=1
    )
    subjects_w1 = [l.subject for l in wed_w1]
    assert "Зустріч з адміністрацією факультету" in subjects_w1
    assert "НаУКМА крізь століття: від Сагайдачного до нас" not in subjects_w1

    # Середа 2-го тижня (09.09.2026)
    wed_w2 = schedule_service.get_lessons_for_day_and_week(
        prog_group="1",
        math_group="1",
        ukr_group="5",
        english_group="A53",
        day_of_week=2,
        week_number=2,
        week_type=2
    )
    subjects_w2 = [l.subject for l in wed_w2]
    assert "НаУКМА крізь століття: від Сагайдачного до нас" in subjects_w2
    assert "Зустріч з адміністрацією факультету" not in subjects_w2

    # Середа 3-го тижня (16.09.2026) - жодної разової події не повинно бути
    wed_w3 = schedule_service.get_lessons_for_day_and_week(
        prog_group="1",
        math_group="1",
        ukr_group="5",
        english_group="A53",
        day_of_week=2,
        week_number=3,
        week_type=1
    )
    subjects_w3 = [l.subject for l in wed_w3]
    assert "НаУКМА крізь століття: від Сагайдачного до нас" not in subjects_w3
    assert "Зустріч з адміністрацією факультету" not in subjects_w3


def test_parse_schedule_date_formats():
    from bot.services.schedule_service import parse_schedule_date
    assert parse_schedule_date("9.09") == date(2026, 9, 9)
    assert parse_schedule_date("09.09") == date(2026, 9, 9)
    assert parse_schedule_date("09.09.2026") == date(2026, 9, 9)
    assert parse_schedule_date("01.09.25") == date(2026, 9, 1)
    assert parse_schedule_date("2026-09-11") == date(2026, 9, 11)


def test_week_2_and_3_backup_rooms():
    schedule_service.reload()
    # 1. Перевірка понеділка 2-го тижня (07.09.2026)
    _, l_w2 = schedule_service.get_lessons_for_date(
        prog_group="1", math_group="1", ukr_group="5", english_group="A51",
        target_date=date(2026, 9, 7)
    )
    discr_w2 = next(l for l in l_w2 if l.subject == "Дискретна математика")
    alg_w2 = next(l for l in l_w2 if l.subject == "Алгебра та геометрія")
    assert "запасна: коридор укриття" in discr_w2.room
    assert "запасна: коридор укриття" in alg_w2.room

    # 2. Перевірка понеділка 3-го тижня (14.09.2026) - запасна аудиторія присутня згідно з розкладом 3-го тижня
    _, l_w3 = schedule_service.get_lessons_for_date(
        prog_group="1", math_group="1", ukr_group="5", english_group="A51",
        target_date=date(2026, 9, 14)
    )
    discr_w3 = next(l for l in l_w3 if l.subject == "Дискретна математика")
    alg_w3 = next(l for l in l_w3 if l.subject == "Алгебра та геометрія")
    assert "запасна: коридор укриття" in discr_w3.room
    assert "запасна: коридор укриття" in alg_w3.room

    # 3. Перевірка вівторка 3-го тижня (15.09.2026) для мов програмування
    _, l_tue_w3 = schedule_service.get_lessons_for_date(
        prog_group="1", math_group="1", ukr_group="5", english_group="A51",
        target_date=date(2026, 9, 15)
    )
    prog_tue = next(l for l in l_tue_w3 if l.subject == "Мови програмування")
    assert "запасна: музей - укриття" in prog_tue.room

    # 4. Перевірка четверга 3-го тижня (17.09.2026) для гр. 5 мов програмування о 08:30
    _, l_thu_w3 = schedule_service.get_lessons_for_date(
        prog_group="5", math_group="1", ukr_group="5", english_group="A51",
        target_date=date(2026, 9, 17)
    )
    prog_thu_5 = next(l for l in l_thu_w3 if l.subject == "Мови програмування" and l.group == "5")
    assert prog_thu_5.start_time == "08:30"
    assert "запасна: електроніка (001)" in prog_thu_5.room

    # 5. Перевірка суботи 3-го тижня (19.09.2026) для матаналізу
    _, l_sat_w3 = schedule_service.get_lessons_for_date(
        prog_group="1", math_group="1", ukr_group="5", english_group="A51",
        target_date=date(2026, 9, 19)
    )
    math_sat_w3 = next(l for l in l_sat_w3 if l.subject == "Математичний аналіз")
    assert "запасна: Музей-укриття" in math_sat_w3.room

    # 6. Перевірка понеділка 4-го тижня (21.09.2026) - запасної немає
    _, l_w4 = schedule_service.get_lessons_for_date(
        prog_group="1", math_group="1", ukr_group="5", english_group="A51",
        target_date=date(2026, 9, 21)
    )
    discr_w4 = next(l for l in l_w4 if l.subject == "Дискретна математика")
    assert "запасна" not in discr_w4.room


def test_management_course_filtering():
    schedule_service.reload()
    target_date = date(2026, 9, 14)  # Понеділок 3-го тижня

    # 1. Якщо has_management=False -> курс не відображається
    _, lessons_no = schedule_service.get_lessons_for_date(
        prog_group="1", math_group="1", ukr_group="5", english_group="A51",
        target_date=target_date, has_management=False
    )
    subjects_no = [l.subject for l in lessons_no]
    assert "Менеджмент та персональна ефективність" not in subjects_no

    # 2. Якщо has_management=True -> курс відображається
    _, lessons_yes = schedule_service.get_lessons_for_date(
        prog_group="1", math_group="1", ukr_group="5", english_group="A51",
        target_date=target_date, has_management=True
    )
    subjects_yes = [l.subject for l in lessons_yes]
    assert "Менеджмент та персональна ефективність" in subjects_yes


def test_physical_education_injection():
    schedule_service.reload()
    target_date = date(2026, 9, 15)  # Вівторок (day_of_week=1)
    pe_slots = [{"day_of_week": 1, "start_time": "10:00", "end_time": "11:20"}]

    # 1. Без слотів
    _, lessons_no = schedule_service.get_lessons_for_date(
        prog_group="1", math_group="1", ukr_group="5", english_group="A51",
        target_date=target_date, pe_slots=None
    )
    assert not any(l.subject == "Фізичне виховання" for l in lessons_no)

    # 2. Зі слотом у вівторок
    _, lessons_yes = schedule_service.get_lessons_for_date(
        prog_group="1", math_group="1", ukr_group="5", english_group="A51",
        target_date=target_date, pe_slots=pe_slots
    )
    pe_lesson = next((l for l in lessons_yes if l.subject == "Фізичне виховання"), None)
    assert pe_lesson is not None
    assert pe_lesson.start_time == "10:00"
    assert pe_lesson.end_time == "11:20"
    assert pe_lesson.room == "Спорткомплекс"
    assert pe_lesson.type_emoji == "🏃"


def test_week_5_backup_rooms():
    schedule_service.reload()

    # 1. Понеділок 5-го тижня (28.09.2026)
    _, l_mon_w5 = schedule_service.get_lessons_for_date(
        prog_group="1", math_group="1", ukr_group="5", english_group="A51",
        target_date=date(2026, 9, 28)
    )
    discr_mon = next(l for l in l_mon_w5 if l.subject == "Дискретна математика")
    alg_mon = next(l for l in l_mon_w5 if l.subject == "Лінійна алгебра та аналітична геометрія")
    assert "запасна: онлайн" in discr_mon.room
    assert "запасна: онлайн" in alg_mon.room

    # 2. Вівторок 5-го тижня (29.09.2026)
    # Гр. 1
    _, l_tue_1 = schedule_service.get_lessons_for_date(
        prog_group="1", math_group="1", ukr_group="5", english_group="A51",
        target_date=date(2026, 9, 29)
    )
    alg_tue_1 = next(l for l in l_tue_1 if l.subject == "Лінійна алгебра та аналітична геометрія")
    assert "запасна: укриття (003)" in alg_tue_1.room
    prog_tue = next(l for l in l_tue_1 if l.subject == "Мови програмування")
    assert "запасна: онлайн/ коридор-укриття" in prog_tue.room

    # Гр. 2
    _, l_tue_2 = schedule_service.get_lessons_for_date(
        prog_group="2", math_group="2", ukr_group="5", english_group="A51",
        target_date=date(2026, 9, 29)
    )
    alg_tue_2 = next(l for l in l_tue_2 if l.subject == "Лінійна алгебра та аналітична геометрія")
    assert "запасна: укриття (003)" in alg_tue_2.room

    # Гр. 3
    _, l_tue_3 = schedule_service.get_lessons_for_date(
        prog_group="3", math_group="3", ukr_group="5", english_group="A51",
        target_date=date(2026, 9, 29)
    )
    alg_tue_3 = next(l for l in l_tue_3 if l.subject == "Лінійна алгебра та аналітична геометрія")
    assert "запасна: електроніка (001)" in alg_tue_3.room

    # 3. Середа 5-го тижня (30.09.2026) для гр. 3
    _, l_wed_3 = schedule_service.get_lessons_for_date(
        prog_group="3", math_group="3", ukr_group="5", english_group="A51",
        target_date=date(2026, 9, 30)
    )
    discr_wed_3 = next(l for l in l_wed_3 if l.subject == "Дискретна математика")
    assert "запасна: коридор-укриття" in discr_wed_3.room

    # 4. Четвер 5-го тижня (01.10.2026)
    # Гр. 5: о 08:30 укриття (003)
    _, l_thu_5 = schedule_service.get_lessons_for_date(
        prog_group="5", math_group="1", ukr_group="5", english_group="A51",
        target_date=date(2026, 10, 1)
    )
    prog_thu_5 = next(l for l in l_thu_5 if l.subject == "Мови програмування" and l.group == "5")
    assert prog_thu_5.start_time == "08:30"
    assert "запасна: укриття (003)" in prog_thu_5.room

    # Гр. 2: о 10:00 укриття (003)
    _, l_thu_2 = schedule_service.get_lessons_for_date(
        prog_group="2", math_group="2", ukr_group="5", english_group="A51",
        target_date=date(2026, 10, 1)
    )
    prog_thu_2 = next(l for l in l_thu_2 if l.subject == "Мови програмування" and l.group == "2")
    assert "запасна: укриття (003)" in prog_thu_2.room

    # Гр. 1: о 11:40 коридор-укриття
    _, l_thu_1 = schedule_service.get_lessons_for_date(
        prog_group="1", math_group="1", ukr_group="5", english_group="A51",
        target_date=date(2026, 10, 1)
    )
    prog_thu_1 = next(l for l in l_thu_1 if l.subject == "Мови програмування" and l.group == "1")
    assert "запасна: коридор-укриття" in prog_thu_1.room

    # Гр. 3: о 11:40 укриття (003)
    _, l_thu_3 = schedule_service.get_lessons_for_date(
        prog_group="3", math_group="3", ukr_group="5", english_group="A51",
        target_date=date(2026, 10, 1)
    )
    prog_thu_3 = next(l for l in l_thu_3 if l.subject == "Мови програмування" and l.group == "3")
    assert "запасна: укриття (003)" in prog_thu_3.room

    # Гр. 4: о 13:30 3Д друк
    _, l_thu_4 = schedule_service.get_lessons_for_date(
        prog_group="4", math_group="1", ukr_group="5", english_group="A51",
        target_date=date(2026, 10, 1)
    )
    prog_thu_4 = next(l for l in l_thu_4 if l.subject == "Мови програмування" and l.group == "4")
    assert "запасна: 3Д друк" in prog_thu_4.room

    # Четвер лекція з ОНС залишається на 5 тижні
    ons_thu = [l for l in l_thu_1 if "національного супротиву" in l.subject]
    assert len(ons_thu) == 2

    # 5. П'ятниця 5-го тижня (02.10.2026) для гр. 3
    _, l_fri_3 = schedule_service.get_lessons_for_date(
        prog_group="3", math_group="3", ukr_group="5", english_group="A51",
        target_date=date(2026, 10, 2)
    )
    math_fri_3 = next(l for l in l_fri_3 if l.subject == "Математичний аналіз")
    assert "запасна: коридор-укриття" in math_fri_3.room

    # 6. Субота 5-го тижня (03.10.2026) для матаналізу
    _, l_sat_w5 = schedule_service.get_lessons_for_date(
        prog_group="1", math_group="1", ukr_group="5", english_group="A51",
        target_date=date(2026, 10, 3)
    )
    math_sat_w5 = next(l for l in l_sat_w5 if l.subject == "Математичний аналіз")
    assert "запасна: Музей-укриття" in math_sat_w5.room


def test_ons_practice_cancellation_oct_3():
    schedule_service.reload()
    # 03.10.2026 - субота 5-го тижня. Практик з ОНС НЕ повинно бути!
    _, l_sat_oct3 = schedule_service.get_lessons_for_date(
        prog_group="1", math_group="1", ukr_group="5", english_group="A51",
        target_date=date(2026, 10, 3)
    )
    ons_practices_oct3 = [
        l for l in l_sat_oct3
        if "національного супротиву" in l.subject.lower()
    ]
    assert len(ons_practices_oct3) == 0, f"Expected 0 ONS practices on 03.10, got: {ons_practices_oct3}"

    # 10.10.2026 - субота 6-го тижня. Практики з ОНС ПОВИННІ бути!
    _, l_sat_oct10 = schedule_service.get_lessons_for_date(
        prog_group="1", math_group="1", ukr_group="5", english_group="A51",
        target_date=date(2026, 10, 10)
    )
    ons_practices_oct10 = [
        l for l in l_sat_oct10
        if "національного супротиву" in l.subject.lower()
    ]
    assert len(ons_practices_oct10) > 0, "Expected ONS practices on 10.10 (week 6)"



