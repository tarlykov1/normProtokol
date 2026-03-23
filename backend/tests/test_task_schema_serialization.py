from app.schemas.common import TaskRead


def test_taskread_accepts_string_topic_candidates():
    payload = {
        "id": 10,
        "protocol_id": 4,
        "topic_id": None,
        "source_fragment": "Фрагмент",
        "normalized_text": "Текст задачи",
        "topic_auto_candidate": "Продажи",
        "topic_candidate_list": ["Продажи", "Маркетинг"],
        "assignee_raw": "Иванов И.И.",
        "assignee_b24_id": None,
        "assignee_b24_name": None,
        "deadline_raw": "01.04.2026",
        "deadline_iso": "2026-04-01",
        "status": "draft",
        "warnings": [],
        "errors": [],
        "order_index": 1,
        "bitrix_task_id": None,
    }

    task = TaskRead.model_validate(payload)

    assert task.topic_candidate_list == ["Продажи", "Маркетинг"]


def test_taskread_converts_dict_topic_candidates_to_titles():
    payload = {
        "id": 11,
        "protocol_id": 4,
        "topic_id": None,
        "source_fragment": "Фрагмент",
        "normalized_text": "Текст задачи",
        "topic_auto_candidate": "Продажи",
        "topic_candidate_list": [{"title": "Продажи", "score": 2}, {"title": "Маркетинг", "score": 1}],
        "assignee_raw": "Иванов И.И.",
        "assignee_b24_id": None,
        "assignee_b24_name": None,
        "deadline_raw": "01.04.2026",
        "deadline_iso": "2026-04-01",
        "status": "draft",
        "warnings": [],
        "errors": [],
        "order_index": 1,
        "bitrix_task_id": None,
    }

    task = TaskRead.model_validate(payload)

    assert task.topic_candidate_list == ["Продажи", "Маркетинг"]
