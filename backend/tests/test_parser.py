from app.services.parser.task_extractor import detect_topic, extract_task_candidates


def test_detect_topic():
    topics = [{"title": "ИТ", "keywords": ["сервер", "интеграция"]}]
    title, variants, confidence = detect_topic("Нужно подготовить сервер и интеграцию", topics)
    assert title == "ИТ"
    assert variants
    assert confidence > 0


def test_extract_task_candidates():
    chunks = ["Обсудили общие вопросы", "Поручить Иванов И.И. подготовить отчет до 21.03.2026"]
    candidates = extract_task_candidates(chunks)
    assert len(candidates) == 1
    assert candidates[0]["assignee_raw"] == "Иванов И.И."
    assert candidates[0]["deadline_raw"] == "21.03.2026"
