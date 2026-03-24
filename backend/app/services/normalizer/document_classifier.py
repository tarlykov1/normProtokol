import re

from app.models.enums import ProtocolType


MEETING_PATTERNS = [
    re.compile(r"\bмемо\b", re.IGNORECASE),
    re.compile(r"мемо\s+рабочей\s+встреч", re.IGNORECASE),
    re.compile(r"\bрешили\b", re.IGNORECASE),
]
PREPARATION_PATTERNS = [
    re.compile(r"мемо\s+подготовк", re.IGNORECASE),
    re.compile(r"задачи\s+по\s+вопросу\s*\d+", re.IGNORECASE),
]
MIXED_PATTERNS = [
    re.compile(r"\bотметили\b", re.IGNORECASE),
    re.compile(r"обсуждение\s+проблем", re.IGNORECASE),
    re.compile(r"предложения\s+по\s+улучшению", re.IGNORECASE),
]
HIERARCHICAL_PATTERNS = [
    re.compile(r"\bкластер\b", re.IGNORECASE),
    re.compile(r"\bтема\b", re.IGNORECASE),
    re.compile(r"вопрос\s+вне\s+повестки", re.IGNORECASE),
    re.compile(r"решение\s+по\s+итогам\s+рабочей\s+встреч", re.IGNORECASE),
]


def classify_document(chunks: list[str]) -> str:
    text = "\n".join(chunks)
    if any(p.search(text) for p in PREPARATION_PATTERNS):
        return ProtocolType.memo_preparation.value
    if any(p.search(text) for p in HIERARCHICAL_PATTERNS):
        return ProtocolType.memo_hierarchical.value
    if any(p.search(text) for p in MIXED_PATTERNS) and re.search(r"\bрешили\b", text, re.IGNORECASE):
        return ProtocolType.memo_mixed_sections.value
    if any(p.search(text) for p in MEETING_PATTERNS):
        return ProtocolType.memo_meeting.value
    return ProtocolType.simple.value
