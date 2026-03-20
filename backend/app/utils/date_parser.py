import re
from datetime import date, datetime, timedelta, timezone

_DATE_PATTERNS = [
    re.compile(r"\b(?P<d>\d{2})\.(?P<m>\d{2})\.(?P<y>\d{4})\b"),
    re.compile(r"\b(?P<d>\d{2})\.(?P<m>\d{2})\.(?P<y>\d{2})\b"),
]

_WORD_PATTERNS = {
    "сегодня": 0,
    "завтра": 1,
    "послезавтра": 2,
}


def parse_deadline(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, None
    text = value.strip().lower()

    for pattern in _DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        day = int(match.group("d"))
        month = int(match.group("m"))
        year = int(match.group("y"))
        if year < 100:
            year += 2000
        try:
            parsed = date(year, month, day)
            return match.group(0), parsed.isoformat()
        except ValueError:
            return match.group(0), None

    for word, delta in _WORD_PATTERNS.items():
        if word in text:
            parsed = datetime.now(timezone.utc).date() + timedelta(days=delta)
            return word, parsed.isoformat()

    return None, None
