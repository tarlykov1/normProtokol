import json
import re
from pathlib import Path

from app.services.topics.matcher import match_topic
from app.utils.date_parser import parse_deadline

ASSIGNEE_PATTERN = re.compile(r"\b([А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.[А-ЯЁ]\.)\b")


def load_task_keywords(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload.get("keywords", [])


def extract_task_candidates(
    chunks: list[str],
    topic_dictionary: list[dict],
    task_keywords: list[str],
    topic_threshold: float,
) -> list[dict]:
    tasks: list[dict] = []
    lowered_keywords = [k.lower() for k in task_keywords]

    for idx, chunk in enumerate(chunks):
        lowered = chunk.lower()
        if not any(word in lowered for word in lowered_keywords):
            continue

        context = " ".join(chunks[max(0, idx - 1): min(len(chunks), idx + 2)])
        match = match_topic(context, topic_dictionary, threshold=topic_threshold)
        assignee_match = ASSIGNEE_PATTERN.search(context)
        raw_deadline, iso_deadline = parse_deadline(context)

        warnings = []
        if len(chunk.split()) < 4:
            warnings.append("Low confidence task detection")
        if not raw_deadline:
            warnings.append("Deadline not recognized")

        tasks.append(
            {
                "source_fragment": context,
                "normalized_text": chunk.strip(),
                "topic_auto_candidate": match.best_candidate,
                "topic_candidate_list": match.candidates,
                "assignee_raw": assignee_match.group(1) if assignee_match else None,
                "deadline_raw": raw_deadline,
                "deadline_iso": iso_deadline,
                "status": "needs_confirmation",
                "warnings": warnings,
                "errors": [],
                "order_index": idx,
                "topic_confidence": match.confidence,
            }
        )
    return tasks
