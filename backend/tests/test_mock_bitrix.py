import json

from app.services.bitrix.bitrix_service import MockBitrixService


def test_mock_bitrix(tmp_path):
    users = tmp_path / "users.json"
    users.write_text(json.dumps([{"id": "1", "name": "Иванов И.И."}], ensure_ascii=False), encoding="utf-8")
    service = MockBitrixService(users)
    assert service.validate_user("1")
    assert service.search_users("иванов")
