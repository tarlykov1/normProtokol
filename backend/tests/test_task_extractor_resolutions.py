from app.services.normalizer.task_extractor import extract_task_candidates


def test_extract_tasks_from_reshili_section():
    chunks = [
        "ПРОТОКОЛ",
        "РЕШИЛИ:",
        "Проект 244 (Цифровизация):",
        "Подготовить реестр интеграций по филиалам.",
        "Исполнитель: Иванов И.И.",
        "Срок: 01.04.2026",
        "Проект 427 (Согласование):",
        "Направить финальную редакцию регламента.",
        "Исполнитель: Петров П.П.",
        "Срок: 03.04.2026",
        "Проект 153 (Пилот):",
        "Подготовить план-график пилота.",
        "Исполнитель: Сидоров С.С.",
        "Срок: 05.04.2026",
        "Обновить перечень рисков по пилоту.",
        "Исполнитель: Сидоров С.С.",
        "Срок: 07.04.2026",
        "Проект 441 (Инфраструктура):",
        "Собрать потребности площадок.",
        "Исполнитель: Козлов К.К.",
        "Срок: 09.04.2026",
        "Согласовать смету инфраструктурного этапа.",
        "Исполнитель: Козлов К.К.",
        "Срок: 11.04.2026",
        "Проекты 139 и 363 (Сервисы):",
        "Подготовить единый статус-отчет по внедрению.",
        "Исполнитель: Смирнова М.М.",
        "Срок: 15.04.2026",
    ]
    topic_dictionary = [
        {"id": "t244", "title": "Проект 244", "keywords": ["проект 244", "244"], "synonyms": []},
        {"id": "t427", "title": "Проект 427", "keywords": ["проект 427", "427"], "synonyms": []},
        {"id": "t153", "title": "Проект 153", "keywords": ["проект 153", "153"], "synonyms": []},
        {"id": "t441", "title": "Проект 441", "keywords": ["проект 441", "441"], "synonyms": []},
        {"id": "t139_363", "title": "Проекты 139 и 363", "keywords": ["139", "363"], "synonyms": []},
    ]

    tasks = extract_task_candidates(chunks, topic_dictionary, task_keywords=[], topic_threshold=0.1)
    real_tasks = [task for task in tasks if task["item_kind"] == "task"]

    assert len(real_tasks) == 7
    assert [task["topic_auto_candidate"] for task in real_tasks] == [
        "Проект 244",
        "Проект 427",
        "Проект 153",
        "Проект 153",
        "Проект 441",
        "Проект 441",
        "Проекты 139 и 363",
    ]
    assert real_tasks[0]["assignee_raw"] == "Иванов И.И."
    assert real_tasks[0]["deadline_raw"] == "01.04.2026"
    assert real_tasks[0]["deadline_iso"] == "2026-04-01"
    assert real_tasks[0]["topic_candidate_list"] == ["Проект 244"]


def test_extract_tasks_from_numbered_reshili_section():
    chunks = [
        "Повестка встречи",
        "1) РЕШИЛИ:",
        "1. Проект 244 (Цифровизация):",
        "Подготовить реестр интеграций по филиалам.",
        "Исполнитель: Иванов И.И.",
        "Срок: 01.04.2026",
        "2. Проекты 139 и 363 (Сервисы):",
        "Подготовить единый статус-отчет по внедрению.",
        "Исполнитель: Смирнова М.М.",
        "Срок: 15.04.2026",
    ]
    topic_dictionary = [
        {"id": "t244", "title": "Проект 244", "keywords": ["проект 244", "244"], "synonyms": []},
        {"id": "t139_363", "title": "Проекты 139 и 363", "keywords": ["139", "363"], "synonyms": []},
    ]

    tasks = extract_task_candidates(chunks, topic_dictionary, task_keywords=[], topic_threshold=0.1)
    real_tasks = [task for task in tasks if task["item_kind"] == "task"]

    assert len(real_tasks) == 2
    assert real_tasks[0]["topic_auto_candidate"] == "Проект 244"
    assert real_tasks[0]["normalized_text"] == "Подготовить реестр интеграций по филиалам."
    assert real_tasks[0]["topic_candidate_list"] == ["Проект 244"]
    assert real_tasks[1]["topic_auto_candidate"] == "Проекты 139 и 363"
    assert real_tasks[1]["assignee_raw"] == "Смирнова М.М."
    assert real_tasks[1]["deadline_iso"] == "2026-04-15"


def test_extracts_agenda_items_inside_reshili_and_skips_not_discussed_as_task():
    chunks = [
        "РЕШИЛИ:",
        "1. Вопрос по интеграции:",
        "Подготовить реестр интеграций.",
        "Исполнитель: Иванов И.И., Петров П.П.",
        "Срок: 01.04.2026",
        "2. Вопрос по архиву (не обсуждался).",
    ]
    tasks = extract_task_candidates(chunks, topic_dictionary=[], task_keywords=[], topic_threshold=0.1)

    agenda_items = [task for task in tasks if task["item_kind"] in {"agenda", "skipped_agenda"}]
    real_tasks = [task for task in tasks if task["item_kind"] == "task"]

    assert len(agenda_items) == 2
    assert len(real_tasks) == 1
    assert real_tasks[0]["assignees_display"] == "Иванов И.И., Петров П.П."
    assert agenda_items[1]["skipped_discussion_flag"] is True


def test_hierarchical_numbering_creates_exactly_three_root_tasks_and_keeps_nested_points_in_body():
    chunks = [
        "РЕШИЛИ:",
        "1. Усилить и систематизировать работу по контролю рейтинга ВЖГ.",
        "1.1. Сформировать ежемесячный график выездов.",
        "1.2. Сформировать чек-лист контрольных мероприятий.",
        "Исполнитель: Башкатова М.Г.",
        "2. Доработать подход по информированию рабочих.",
        "Исполнитель: Башкатова М.Г.",
        "3. Усилить и систематизировать работу психологов/адаптологов.",
        "3.1. Сформировать график посещения.",
        "Перезагрузить работу с СПК.",
        "Исполнитель: Башкатова М.Г.",
    ]

    tasks = extract_task_candidates(chunks, topic_dictionary=[], task_keywords=[], topic_threshold=0.1)
    real_tasks = [task for task in tasks if task["item_kind"] == "task"]

    assert len(real_tasks) == 3
    assert len(real_tasks) != 1
    assert len(real_tasks) != 5
    assert len(real_tasks) != 6

    task_1, task_2, task_3 = real_tasks

    assert "1.1. Сформировать ежемесячный график выездов." in task_1["normalized_text"]
    assert "1.2. Сформировать чек-лист контрольных мероприятий." in task_1["normalized_text"]

    assert "1. Усилить и систематизировать работу по контролю рейтинга ВЖГ." not in task_2["normalized_text"]
    assert "3. Усилить и систематизировать работу психологов/адаптологов." not in task_2["normalized_text"]
    assert task_2["normalized_text"] == "Доработать подход по информированию рабочих."

    assert "3.1. Сформировать график посещения." in task_3["normalized_text"]
    assert "Перезагрузить работу с СПК." in task_3["normalized_text"]

    for task in real_tasks:
        assert task["assignee_raw"] == "Башкатова М.Г."
        assert task["deadline_iso"] is None
        assert "У задачи не указан срок. Добавьте дату в формате ДД.ММ.ГГГГ." in task["errors"]


def test_hierarchical_numbering_works_when_resolution_is_single_multiline_chunk():
    chunks = [
        "РЕШИЛИ:\n"
        "1. Усилить и систематизировать работу по контролю рейтинга ВЖГ.\n"
        "1.1. Сформировать ежемесячный график контроля.\n"
        "1.2. Сформировать чек-лист контрольных мероприятий.\n"
        "Исполнитель: Башкатова М.Г.\n\n"
        "2. Доработать подход по информированию рабочих.\n"
        "Исполнитель: Башкатова М.Г.\n\n"
        "3. Усилить и систематизировать работу психологов / адаптологов.\n"
        "3.1. Сформировать график посещения.\n"
        "Перезагрузить работу с СПК.\n"
        "Исполнитель: Башкатова М.Г."
    ]

    tasks = extract_task_candidates(chunks, topic_dictionary=[], task_keywords=[], topic_threshold=0.1)
    real_tasks = [task for task in tasks if task["item_kind"] == "task"]

    assert len(real_tasks) == 3
    assert [task["assignee_raw"] for task in real_tasks] == ["Башкатова М.Г.", "Башкатова М.Г.", "Башкатова М.Г."]
    assert "1.1. Сформировать ежемесячный график контроля." in real_tasks[0]["normalized_text"]
    assert "1.2. Сформировать чек-лист контрольных мероприятий." in real_tasks[0]["normalized_text"]
    assert real_tasks[1]["normalized_text"] == "Доработать подход по информированию рабочих."
    assert "3.1. Сформировать график посещения." in real_tasks[2]["normalized_text"]
    assert "Перезагрузить работу с СПК." in real_tasks[2]["normalized_text"]
    for task in real_tasks:
        assert task["deadline_iso"] is None
        assert "У задачи не указан срок. Добавьте дату в формате ДД.ММ.ГГГГ." in task["errors"]
