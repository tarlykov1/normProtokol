from app.services.topics.matcher import match_topic


def test_topic_matcher():
    dictionary = [
        {"id": "topic_1", "title": "Проект 244", "keywords": ["244"], "synonyms": ["проект 244"]}
    ]
    result = match_topic("Обсудили проект 244 и интеграцию", dictionary, threshold=0.1)
    assert result.best_candidate == "Проект 244"
    assert result.confidence > 0
