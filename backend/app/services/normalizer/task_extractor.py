import json
import re
from pathlib import Path

from app.services.topics.matcher import match_topic
from app.utils.date_parser import parse_deadline

ASSIGNEE_PATTERN = re.compile(r"\b([А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.[А-ЯЁ]\.)\b")
RESOLUTION_HEADER_PATTERN = re.compile(r"^\s*решили\s*:?\s*$", re.IGNORECASE)
PROJECT_HEADER_PATTERN = re.compile(r"^\s*проекты?\b[^:]*:\s*$", re.IGNORECASE)
ASSIGNEE_LINE_PATTERN = re.compile(r"^\s*исполнитель\s*:\s*(?P<value>.+?)\s*$", re.IGNORECASE)
DEADLINE_LINE_PATTERN = re.compile(r"^\s*срок\s*:\s*(?P<value>.+?)\s*$", re.IGNORECASE)
LIST_PREFIX_PATTERN = re.compile(r"^\s*(?:\d+[\).:-]\s*|[-–—•]\s*)")


def _normalize_topic_candidates(candidates: list[dict]) -> list[str]:
    return [candidate["title"] for candidate in candidates if candidate.get("title")]


def _clean_line_prefix(line: str) -> str:
    return LIST_PREFIX_PATTERN.sub("", line).strip()


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
    resolved_tasks = _extract_tasks_from_resolutions(chunks, topic_dictionary, topic_threshold)
    if resolved_tasks:
        return resolved_tasks

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
                "topic_candidate_list": _normalize_topic_candidates(match.candidates),
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


def _extract_tasks_from_resolutions(chunks: list[str], topic_dictionary: list[dict], topic_threshold: float) -> list[dict]:
    start_idx = next((idx for idx, line in enumerate(chunks) if RESOLUTION_HEADER_PATTERN.search(_clean_line_prefix(line))), None)
    if start_idx is None:
        return []

    tasks: list[dict] = []
    current_topic_title: str | None = None
    current_body: list[str] = []
    current_assignee: str | None = None
    current_deadline_raw: str | None = None
    current_deadline_iso: str | None = None
    current_start_index = start_idx + 1

    def flush_current_task() -> None:
        nonlocal current_body, current_assignee, current_deadline_raw, current_deadline_iso, current_start_index
        normalized_text = " ".join(part.strip() for part in current_body if part.strip()).strip()
        if not normalized_text and not current_assignee and not current_deadline_raw:
            return
        context_parts = []
        if current_topic_title:
            context_parts.append(current_topic_title)
        if normalized_text:
            context_parts.append(normalized_text)
        if current_assignee:
            context_parts.append(f"Исполнитель: {current_assignee}")
        if current_deadline_raw:
            context_parts.append(f"Срок: {current_deadline_raw}")
        source_fragment = "\n".join(context_parts)

        context_for_topic = " ".join(context_parts)
        topic_match = match_topic(context_for_topic, topic_dictionary, threshold=topic_threshold)
        topic_auto_candidate = topic_match.best_candidate or current_topic_title
        topic_confidence = topic_match.confidence if topic_match.best_candidate else (1.0 if current_topic_title else 0.0)
        if topic_match.candidates:
            topic_candidate_list = _normalize_topic_candidates(topic_match.candidates)
        elif current_topic_title:
            topic_candidate_list = [current_topic_title]
        else:
            topic_candidate_list = []

        warnings: list[str] = []
        if not current_assignee:
            warnings.append("Assignee not recognized")
        if not current_deadline_raw:
            warnings.append("Deadline not recognized")

        tasks.append(
            {
                "source_fragment": source_fragment,
                "normalized_text": normalized_text or (current_topic_title or ""),
                "topic_auto_candidate": topic_auto_candidate,
                "topic_candidate_list": topic_candidate_list,
                "assignee_raw": current_assignee,
                "deadline_raw": current_deadline_raw,
                "deadline_iso": current_deadline_iso,
                "status": "needs_confirmation",
                "warnings": warnings,
                "errors": [],
                "order_index": current_start_index,
                "topic_confidence": topic_confidence,
            }
        )

    for idx in range(start_idx + 1, len(chunks)):
        line = _clean_line_prefix(chunks[idx])
        if not line:
            continue

        if PROJECT_HEADER_PATTERN.match(line):
            flush_current_task()
            current_topic_title = line.rstrip(":").strip()
            current_body = []
            current_assignee = None
            current_deadline_raw = None
            current_deadline_iso = None
            current_start_index = idx
            continue

        assignee_match = ASSIGNEE_LINE_PATTERN.match(line)
        if assignee_match:
            current_assignee = assignee_match.group("value").strip()
            continue

        deadline_match = DEADLINE_LINE_PATTERN.match(line)
        if deadline_match:
            deadline_value = deadline_match.group("value").strip()
            parsed_deadline_raw, current_deadline_iso = parse_deadline(deadline_value)
            current_deadline_raw = parsed_deadline_raw or deadline_value
            flush_current_task()
            current_body = []
            current_assignee = None
            current_deadline_raw = None
            current_deadline_iso = None
            current_start_index = idx + 1
            continue

        if current_topic_title is None:
            continue
        current_body.append(line)

    flush_current_task()
    return tasks


def extract_simple_task_candidates(
    chunks: list[str],
    topic_dictionary: list[dict],
    task_keywords: list[str],
    topic_threshold: float,
) -> list[dict]:
    tasks = extract_task_candidates(chunks, topic_dictionary, task_keywords, topic_threshold)
    if tasks:
        return tasks

    fallback_tasks: list[dict] = []
    lowered_keywords = [k.lower() for k in task_keywords]
    for idx, chunk in enumerate(chunks):
        cleaned = _clean_line_prefix(chunk).strip()
        if len(cleaned.split()) < 3:
            continue
        lowered = cleaned.lower()
        if lowered_keywords and not any(word in lowered for word in lowered_keywords) and not LIST_PREFIX_PATTERN.match(chunk):
            continue

        assignee_match = ASSIGNEE_PATTERN.search(cleaned)
        raw_deadline, iso_deadline = parse_deadline(cleaned)
        warnings: list[str] = []
        if not assignee_match:
            warnings.append("Исполнитель не распознан автоматически")
        if not raw_deadline:
            warnings.append("Срок не распознан автоматически")

        fallback_tasks.append(
            {
                "source_fragment": cleaned,
                "normalized_text": cleaned,
                "topic_auto_candidate": None,
                "topic_candidate_list": [],
                "assignee_raw": assignee_match.group(1) if assignee_match else None,
                "deadline_raw": raw_deadline,
                "deadline_iso": iso_deadline,
                "status": "needs_confirmation",
                "warnings": warnings,
                "errors": [],
                "order_index": idx,
                "topic_confidence": 0.0,
            }
        )
    return fallback_tasks
