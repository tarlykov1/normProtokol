from app.utils.date_parser import parse_deadline


def test_parse_deadline_numeric():
    raw, iso = parse_deadline("Срок 21.03.2026")
    assert raw == "21.03.2026"
    assert iso == "2026-03-21"
