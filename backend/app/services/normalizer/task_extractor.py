import json
import re
from pathlib import Path

from app.models.enums import TaskStatus
from app.services.topics.matcher import match_topic
from app.utils.date_parser import parse_deadline

RESOLUTION_HEADER_PATTERN = re.compile(r"^\s*решили\s*:?\s*$", re.IGNORECASE)
QUESTION_TASK_SECTION_PATTERN = re.compile(r"^\s*задачи\s+по\s+вопросу\s*\d+", re.IGNORECASE)
INFORMATIONAL_SECTION_PATTERNS = [
    re.compile(r"^\s*отметили\s*:?\s*$", re.IGNORECASE),
    re.compile(r"^\s*обсуждение\s+проблем\s*:?\s*$", re.IGNORECASE),
    re.compile(r"^\s*предложения\s+по\s+улучшению\s*:?\s*$", re.IGNORECASE),
]
FOOTER_PATTERN = re.compile(r"^\s*мемо\s+подготовил[аиы]?\b", re.IGNORECASE)
ASSIGNEE_LINE_PATTERN = re.compile(r"^\s*исполнител(?:ь|и)\s*:\s*(?P<value>.*)\s*$", re.IGNORECASE)
DEADLINE_LINE_PATTERN = re.compile(r"^\s*срок\s*:\s*(?P<value>.*)\s*$", re.IGNORECASE)
TASK_START_PATTERN = re.compile(r"^\s*(?:\d+(?!\.\d)[\).:-]\s*|[-–—•]\s+)")
LIST_PREFIX_PATTERN = re.compile(r"^\s*(?:\d+(?!\.\d)[\).:-]\s*|[-–—•]\s*)")
PROJECT_CONTEXT_PATTERN = re.compile(r"^\s*проекты?\b.*:\s*$", re.IGNORECASE)
ROOT_NUMBERED_TASK_PATTERN = re.compile(r"^\s*(?P<num>\d+)\.(?!\d)\s*(?P<body>.+)$")
NESTED_NUMBERED_ITEM_PATTERN = re.compile(r"^\s*(?P<num>\d+(?:\.\d+)+)\.?\s*(?P<body>.+)$")

CONTEXT_PATTERNS = [
    re.compile(r"^\s*кластер\b.*", re.IGNORECASE),
    re.compile(r"^\s*тема\b.*", re.IGNORECASE),
    re.compile(r"^\s*вопрос\s+вне\s+повестки\b.*", re.IGNORECASE),
    re.compile(r"^\s*решение\s+по\s+итогам\s+рабочей\s+встреч\b.*", re.IGNORECASE),
]
NOT_REVIEWED_PATTERN = re.compile(r"^\s*не\s+рассматривали\.?\s*$", re.IGNORECASE)
NOTE_IN_BRACKETS = re.compile(r"\((?P<note>[^)]+)\)")
ASSIGNEE_SPLIT = re.compile(r"\s*(?:,|;|/| и )\s*")
AGENDA_HEADER_LINE_PATTERN = re.compile(r"^[A-ZА-Я0-9].{5,}:$")
NOT_DISCUSSED_PATTERN = re.compile(r"не\s+обсуждал(?:ся|ись)?", re.IGNORECASE)


def load_task_keywords(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload.get("keywords", [])


def _normalize_topic_candidates(candidates: list[dict]) -> list[str]:
    return [candidate["title"] for candidate in candidates if candidate.get("title")]


def _clean_line_prefix(line: str) -> str:
    return LIST_PREFIX_PATTERN.sub("", line).strip()


def _parse_assignees(raw_value: str | None) -> tuple[str | None, list[str], list[str]]:
    if raw_value is None:
        return None, [], []
    raw_value = raw_value.strip()
    if not raw_value:
        return "", [], []

    notes = NOTE_IN_BRACKETS.findall(raw_value)
    cleaned = NOTE_IN_BRACKETS.sub("", raw_value).strip()
    parts = [part.strip() for part in ASSIGNEE_SPLIT.split(cleaned) if part.strip()]
    return cleaned, parts, notes


def _normalize_deadline(raw_value: str | None) -> tuple[str | None, str | None, str, str | None]:
    if raw_value is None:
        return None, None, "empty_deadline", None

    raw = raw_value.strip()
    if not raw:
        return "", None, "empty_deadline", None

    notes = NOTE_IN_BRACKETS.findall(raw)
    cleaned = NOTE_IN_BRACKETS.sub("", raw).strip(" .")
    note = "; ".join(notes) if notes else None

    lowered = cleaned.lower()
    if lowered in {"к исполнению", "исполнить", "по готовности"}:
        return raw, None, "text_deadline", note

    parsed_raw, iso = parse_deadline(cleaned)
    if iso:
        if re.search(r"\b\d{1,2}:\d{2}\b", cleaned):
            return raw, iso, "exact_datetime", note
        if note:
            return raw, iso, "date_with_marker", note
        return raw, iso, "exact_date", note

    return raw, None, "text_deadline", note


def _build_task(
    *,
    body_lines: list[str],
    source_lines: list[str],
    section_name: str,
    parent_context: str | None,
    context_label: str | None,
    assignees_raw: str | None,
    deadline_raw_input: str | None,
    topic_dictionary: list[dict],
    topic_threshold: float,
    order_index: int,
) -> dict | None:
    normalized_text = " ".join(line.strip() for line in body_lines if line.strip()).strip()
    if not normalized_text and not assignees_raw and not deadline_raw_input:
        return None

    normalized_assignees_raw, assignees, assignee_notes = _parse_assignees(assignees_raw)
    assignees_display = ", ".join(assignees) if assignees else None
    deadline_raw, deadline_iso, deadline_kind, deadline_note = _normalize_deadline(deadline_raw_input)

    markers: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []

    if context_label:
        markers.append(context_label)
    if assignee_notes:
        markers.extend([f"assignee_note:{note}" for note in assignee_notes])
    if deadline_note:
        markers.append(f"deadline_note:{deadline_note}")

    if NOT_REVIEWED_PATTERN.match(normalized_text):
        markers.append("not_reviewed")
        return {
            "source_fragment": "\n".join(source_lines),
            "normalized_text": normalized_text,
            "section_name": section_name,
            "parent_context": parent_context,
            "context_label": context_label,
            "assignee_raw": assignees[0] if assignees else None,
            "assignees_raw": normalized_assignees_raw,
            "assignees_normalized": assignees,
            "assignees_display": assignees_display,
            "coordinator": None,
            "deadline_raw": deadline_raw,
            "deadline_iso": deadline_iso,
            "deadline_kind": deadline_kind,
            "deadline_note": deadline_note,
            "markers": markers,
            "item_kind": "skipped_agenda",
            "discussed_flag": False,
            "skipped_discussion_flag": True,
            "topic_auto_candidate": parent_context,
            "topic_candidate_list": [parent_context] if parent_context else [],
            "status": TaskStatus.excluded.value,
            "warnings": ["Пункт отмечен как «Не рассматривали». Подтвердите исключение из публикации."],
            "errors": [],
            "order_index": order_index,
            "topic_confidence": 0.0,
        }

    # Topic matching fallback
    context_for_topic = " ".join([parent_context or "", normalized_text]).strip()
    topic_match = match_topic(context_for_topic, topic_dictionary, threshold=topic_threshold)
    topic_auto_candidate = topic_match.best_candidate or parent_context
    topic_candidate_list = _normalize_topic_candidates(topic_match.candidates) if topic_match.candidates else ([parent_context] if parent_context else [])
    topic_confidence = topic_match.confidence if topic_match.best_candidate else (1.0 if parent_context else 0.0)

    if deadline_kind == "empty_deadline":
        errors.append("У задачи не указан срок. Добавьте дату в формате ДД.ММ.ГГГГ.")
    elif deadline_kind == "text_deadline":
        warnings.append("Срок «к исполнению» не может быть опубликован как календарная дата. Уточните дату или подтвердите нефиксированный срок.")

    if not normalized_text:
        errors.append("Задача содержит только тему или контекст без действия. Доработайте формулировку поручения.")

    status = TaskStatus.extracted.value
    if errors:
        status = TaskStatus.needs_completion.value
    elif warnings:
        status = TaskStatus.needs_review.value

    return {
        "source_fragment": "\n".join(source_lines),
        "normalized_text": normalized_text,
        "section_name": section_name,
        "parent_context": parent_context,
        "context_label": context_label,
        "assignee_raw": assignees[0] if assignees else None,
        "assignees_raw": normalized_assignees_raw,
        "assignees_normalized": assignees,
        "assignees_display": assignees_display,
        "coordinator": None,
        "deadline_raw": deadline_raw,
        "deadline_iso": deadline_iso,
        "deadline_kind": deadline_kind,
        "deadline_note": deadline_note,
        "markers": markers,
        "item_kind": "task",
        "discussed_flag": True,
        "skipped_discussion_flag": False,
        "topic_auto_candidate": topic_auto_candidate,
        "topic_candidate_list": topic_candidate_list,
        "status": status,
        "warnings": warnings,
        "errors": errors,
        "order_index": order_index,
        "topic_confidence": topic_confidence,
    }


def extract_task_candidates(
    chunks: list[str],
    topic_dictionary: list[dict],
    task_keywords: list[str],
    topic_threshold: float,
) -> list[dict]:
    tasks: list[dict] = []
    section_name = "metadata"
    parent_context: str | None = None
    context_label: str | None = None

    current_body: list[str] = []
    current_source: list[str] = []
    current_assignees_raw: str | None = None
    current_deadline_raw: str | None = None
    current_order = 0

    def flush_current() -> None:
        nonlocal current_body, current_source, current_assignees_raw, current_deadline_raw, current_order
        if not current_body and current_assignees_raw is None and current_deadline_raw is None:
            return
        task = _build_task(
            body_lines=current_body,
            source_lines=current_source,
            section_name=section_name,
            parent_context=parent_context,
            context_label=context_label,
            assignees_raw=current_assignees_raw,
            deadline_raw_input=current_deadline_raw,
            topic_dictionary=topic_dictionary,
            topic_threshold=topic_threshold,
            order_index=current_order,
        )
        if task:
            tasks.append(task)
        current_body = []
        current_source = []
        current_assignees_raw = None
        current_deadline_raw = None

    def build_agenda_item(label: str, skipped: bool, order_index: int) -> dict:
        clean_label = label.rstrip(":").strip()
        markers = [context_label] if context_label else []
        if skipped:
            markers.append("not_reviewed")
        return {
            "source_fragment": clean_label,
            "normalized_text": clean_label,
            "section_name": section_name,
            "parent_context": clean_label,
            "context_label": "agenda_from_resolution",
            "assignee_raw": None,
            "assignees_raw": None,
            "assignees_normalized": [],
            "assignees_display": None,
            "coordinator": None,
            "deadline_raw": None,
            "deadline_iso": None,
            "deadline_kind": "empty_deadline",
            "deadline_note": None,
            "markers": markers,
            "item_kind": "skipped_agenda" if skipped else "agenda",
            "discussed_flag": not skipped,
            "skipped_discussion_flag": skipped,
            "topic_auto_candidate": clean_label,
            "topic_candidate_list": [clean_label],
            "status": TaskStatus.excluded.value,
            "warnings": [],
            "errors": [],
            "order_index": order_index,
            "topic_confidence": 0.0,
        }

    expanded_chunks: list[tuple[int, str]] = []
    for idx, chunk in enumerate(chunks):
        lines = chunk.splitlines() or [chunk]
        for line in lines:
            expanded_chunks.append((idx, line))

    for idx, raw_line in expanded_chunks:
        stripped_line = raw_line.strip()
        cleaned_line = _clean_line_prefix(raw_line)
        if not cleaned_line:
            continue
        root_numbered_match = ROOT_NUMBERED_TASK_PATTERN.match(stripped_line)
        nested_numbered_match = NESTED_NUMBERED_ITEM_PATTERN.match(stripped_line)

        if FOOTER_PATTERN.match(cleaned_line):
            flush_current()
            section_name = "footer"
            continue

        if RESOLUTION_HEADER_PATTERN.match(cleaned_line):
            flush_current()
            section_name = "task_section"
            continue

        if (
            section_name == "task_section"
            and not current_body
            and (cleaned_line.endswith(":") or NOT_DISCUSSED_PATTERN.search(cleaned_line))
            and not ASSIGNEE_LINE_PATTERN.match(cleaned_line)
            and not DEADLINE_LINE_PATTERN.match(cleaned_line)
            and (
                AGENDA_HEADER_LINE_PATTERN.match(cleaned_line)
                or TASK_START_PATTERN.match(raw_line)
                or "вопрос" in cleaned_line.lower()
            )
        ):
            flush_current()
            skipped_discussion = bool(NOT_DISCUSSED_PATTERN.search(cleaned_line))
            agenda_item = build_agenda_item(cleaned_line, skipped_discussion, idx)
            tasks.append(agenda_item)
            parent_context = cleaned_line.rstrip(":").strip()
            context_label = "agenda_from_resolution"
            continue

        if QUESTION_TASK_SECTION_PATTERN.match(cleaned_line):
            flush_current()
            section_name = "task_section"
            parent_context = cleaned_line
            context_label = "question_tasks"
            continue

        if any(p.match(cleaned_line) for p in INFORMATIONAL_SECTION_PATTERNS):
            flush_current()
            section_name = "informational"
            continue

        matched_context = next((p for p in CONTEXT_PATTERNS if p.match(cleaned_line)), None)
        if PROJECT_CONTEXT_PATTERN.match(cleaned_line):
            flush_current()
            parent_context = cleaned_line.rstrip(":").strip()
            context_label = "project_context"
            continue

        if matched_context:
            flush_current()
            parent_context = cleaned_line
            if re.search(r"вне\s+повестки", cleaned_line, re.IGNORECASE):
                context_label = "out_of_agenda"
            elif re.search(r"решение\s+по\s+итогам", cleaned_line, re.IGNORECASE):
                context_label = "meeting_resolution_block"
            else:
                context_label = "hierarchical_context"
            continue

        assignee_match = ASSIGNEE_LINE_PATTERN.match(cleaned_line)
        if assignee_match:
            current_assignees_raw = assignee_match.group("value")
            current_source.append(cleaned_line)
            continue

        deadline_match = DEADLINE_LINE_PATTERN.match(cleaned_line)
        if deadline_match:
            current_deadline_raw = deadline_match.group("value")
            current_source.append(cleaned_line)
            flush_current()
            continue

        if section_name in {"informational", "footer", "metadata"}:
            # informational text is not extracted as executable tasks
            continue

        if section_name == "task_section" and root_numbered_match:
            root_text = root_numbered_match.group("body").strip()
            if current_body:
                flush_current()
            if not current_source:
                current_order = idx
            current_body.append(root_text)
            current_source.append(root_text)
            continue

        if section_name == "task_section" and nested_numbered_match and current_body:
            nested_text = f"{nested_numbered_match.group('num')}. {nested_numbered_match.group('body').strip()}"
            current_body.append(nested_text)
            current_source.append(nested_text)
            continue

        if TASK_START_PATTERN.match(raw_line) and current_body:
            flush_current()

        if not current_source:
            current_order = idx

        current_body.append(cleaned_line)
        current_source.append(cleaned_line)

    flush_current()

    if tasks:
        return tasks

    return extract_simple_task_candidates(chunks, topic_dictionary, task_keywords, topic_threshold)


def extract_simple_task_candidates(
    chunks: list[str],
    topic_dictionary: list[dict],
    task_keywords: list[str],
    topic_threshold: float,
) -> list[dict]:
    fallback_tasks: list[dict] = []
    lowered_keywords = [k.lower() for k in task_keywords]
    for idx, chunk in enumerate(chunks):
        cleaned = _clean_line_prefix(chunk).strip()
        if len(cleaned.split()) < 3:
            continue
        lowered = cleaned.lower()
        if lowered_keywords and not any(word in lowered for word in lowered_keywords) and not TASK_START_PATTERN.match(chunk):
            continue

        task = _build_task(
            body_lines=[cleaned],
            source_lines=[cleaned],
            section_name="task_section",
            parent_context=None,
            context_label=None,
            assignees_raw=None,
            deadline_raw_input=None,
            topic_dictionary=topic_dictionary,
            topic_threshold=topic_threshold,
            order_index=idx,
        )
        if task:
            fallback_tasks.append(task)
    return fallback_tasks
