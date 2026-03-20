from dataclasses import dataclass


@dataclass
class Assignee:
    id: str
    name: str


class BitrixService:
    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        self._mock_users = [
            Assignee(id="101", name="Иванов И.И."),
            Assignee(id="102", name="Петров П.П."),
            Assignee(id="103", name="Сидорова А.А."),
            Assignee(id="104", name="Кузнецов Д.Д."),
        ]

    def search_users(self, query: str) -> list[Assignee]:
        q = query.lower().strip()
        return [u for u in self._mock_users if q in u.name.lower() or q in u.id]

    def validate_assignee(self, assignee_id: str) -> bool:
        return any(u.id == assignee_id for u in self._mock_users)

    def create_smart_process(self, protocol_id: int) -> str:
        return f"SP-{protocol_id}-001"

    def create_task(self, protocol_id: int, task_id: int, title: str, assignee_id: str, deadline: str | None) -> str:
        return f"BTX-{protocol_id}-{task_id}"
