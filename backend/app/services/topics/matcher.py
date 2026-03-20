import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TopicMatchResult:
    best_candidate: str | None
    confidence: float
    candidates: list[dict]


def load_topics(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def match_topic(text: str, dictionary: list[dict], threshold: float = 0.34) -> TopicMatchResult:
    lowered = text.lower()
    scored: list[dict] = []
    for item in dictionary:
        score = 0
        for keyword in item.get("keywords", []):
            if keyword.lower() in lowered:
                score += 1
        for synonym in item.get("synonyms", []):
            if synonym.lower() in lowered:
                score += 2
        if score:
            scored.append({"id": item.get("id"), "title": item["title"], "score": score})

    if not scored:
        return TopicMatchResult(best_candidate=None, confidence=0.0, candidates=[])

    scored.sort(key=lambda x: x["score"], reverse=True)
    best = scored[0]
    confidence = min(best["score"] / 5.0, 1.0)
    if confidence < threshold:
        return TopicMatchResult(best_candidate=None, confidence=confidence, candidates=scored)
    return TopicMatchResult(best_candidate=best["title"], confidence=confidence, candidates=scored)
