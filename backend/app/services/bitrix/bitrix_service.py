import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


class BitrixServiceError(Exception):
    """Базовая ошибка Bitrix24."""


class BitrixUnavailableError(BitrixServiceError):
    """Сервис Bitrix24 временно недоступен."""


@dataclass
class Assignee:
    id: str
    name: str
    aliases: list[str] = field(default_factory=list)


class BaseBitrixService(ABC):
    @abstractmethod
    def search_users(self, query: str) -> list[Assignee]: ...

    @abstractmethod
    def validate_user(self, user_id: str) -> bool: ...

    @abstractmethod
    def create_smart_process(self, protocol_payload: dict) -> str: ...

    @abstractmethod
    def create_task(self, task_payload: dict) -> str: ...


class MockBitrixService(BaseBitrixService):
    def __init__(self, users_path: Path):
        with users_path.open("r", encoding="utf-8") as f:
            users = json.load(f)
        self._users = [
            Assignee(
                id=str(u["id"]),
                name=u["name"],
                aliases=[alias for alias in u.get("aliases", []) if isinstance(alias, str)],
            )
            for u in users
        ]

    def search_users(self, query: str) -> list[Assignee]:
        q = query.lower().strip()
        if not q:
            return self._users
        result: list[Assignee] = []
        for user in self._users:
            if q in user.id or q in user.name.lower() or any(q in alias.lower() for alias in user.aliases):
                result.append(user)
        return result

    def validate_user(self, user_id: str) -> bool:
        return any(u.id == str(user_id) for u in self._users)

    def create_smart_process(self, protocol_payload: dict) -> str:
        return f"MOCK-SP-{protocol_payload['protocol_id']}"

    def create_task(self, task_payload: dict) -> str:
        return f"MOCK-TASK-{task_payload['task_id']}"


class RealBitrixService(BaseBitrixService):
    def __init__(self, base_url: str, webhook: str):
        self.base_url = base_url.rstrip("/")
        self.webhook = webhook

    def _post(self, method: str, payload: dict) -> dict:
        import httpx

        url = f"{self.base_url}/{self.webhook}/{method}"
        try:
            response = httpx.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise BitrixUnavailableError("Сервис Bitrix24 временно недоступен") from exc

    def search_users(self, query: str) -> list[Assignee]:
        data = self._post("user.search", {"FILTER": {"FIND": query}})
        return [Assignee(id=str(u["ID"]), name=u.get("NAME", "")) for u in data.get("result", [])]

    def validate_user(self, user_id: str) -> bool:
        users = self.search_users(str(user_id))
        return any(u.id == str(user_id) for u in users)

    def create_smart_process(self, protocol_payload: dict) -> str:
        data = self._post("crm.item.add", {"fields": protocol_payload})
        return str(data.get("result", {}).get("item", {}).get("id"))

    def create_task(self, task_payload: dict) -> str:
        data = self._post("tasks.task.add", {"fields": task_payload})
        return str(data.get("result", {}).get("task", {}).get("id"))
