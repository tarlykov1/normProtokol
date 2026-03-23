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

    assert len(tasks) == 7
    assert [task["topic_auto_candidate"] for task in tasks] == [
        "Проект 244",
        "Проект 427",
        "Проект 153",
        "Проект 153",
        "Проект 441",
        "Проект 441",
        "Проекты 139 и 363",
    ]
    assert tasks[0]["assignee_raw"] == "Иванов И.И."
    assert tasks[0]["deadline_raw"] == "01.04.2026"
    assert tasks[0]["deadline_iso"] == "2026-04-01"
    assert tasks[0]["topic_candidate_list"] == ["Проект 244"]


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

    assert len(tasks) == 2
    assert tasks[0]["topic_auto_candidate"] == "Проект 244"
    assert tasks[0]["normalized_text"] == "Подготовить реестр интеграций по филиалам."
    assert tasks[0]["topic_candidate_list"] == ["Проект 244"]
    assert tasks[1]["topic_auto_candidate"] == "Проекты 139 и 363"
    assert tasks[1]["assignee_raw"] == "Смирнова М.М."
    assert tasks[1]["deadline_iso"] == "2026-04-15"
