import json
import re
from pathlib import Path

from app.core.config import settings

TASK_KEYWORDS = [
    "поручить",
    "подготовить",
    "обеспечить",
    "направить",
    "согласовать",
    "проработать",
    "выполнить",
    "предоставить",
]

DATE_PATTERNS = [
    re.compile(r"\b(\d{2}\.\d{2}\.\d{4})\b"),
    re.compile(r"\b(\d{2}\.\d{2}\.\d{2})\b"),
]
ASSIGNEE_PATTERN = re.compile(r"\b([А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.[А-ЯЁ]\.)\b")


def load_topic_dictionary(path: Path | None = None) -> list[dict]:
    dictionary_path = path or settings.topic_dictionary_path
    with open(dictionary_path, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_topic(text: str, topic_dictionary: list[dict]) -> tuple[str | None, list[dict], float]:
    lowered = text.lower()
    scored: list[dict] = []

    for topic in topic_dictionary:
        score = sum(1 for kw in topic["keywords"] if kw.lower() in lowered)
        if score > 0:
            scored.append({"title": topic["title"], "score": score})

    if not scored:
        return None, [], 0.0

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[0]
    confidence = min(1.0, top["score"] / 3)
    return top["title"], scored[:5], confidence


def parse_deadline(text: str) -> str | None:
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1)
    return None


def parse_assignee(text: str) -> str | None:
    match = ASSIGNEE_PATTERN.search(text)
    return match.group(1) if match else None


def is_task_candidate(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in TASK_KEYWORDS)


def extract_task_candidates(chunks: list[str]) -> list[dict]:
    topic_dict = load_topic_dictionary()
    candidates: list[dict] = []

    for idx, chunk in enumerate(chunks):
        if not is_task_candidate(chunk):
            continue
        topic, topic_candidates, confidence = detect_topic(chunk, topic_dict)
        candidates.append(
            {
                "source_fragment": chunk,
                "normalized_text": chunk,
                "topic_auto_candidate": topic,
                "topic_candidate_list": topic_candidates,
                "assignee_raw": parse_assignee(chunk),
                "deadline_raw": parse_deadline(chunk),
                "status": "parsed",
                "warnings": [],
                "errors": [],
                "order_index": idx,
                "topic_confidence": confidence,
            }
        )

    return candidates
