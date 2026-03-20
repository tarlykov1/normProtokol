from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Protocol Normalizer MVP"
    debug: bool = True
    database_url: str = "sqlite:///./data/app.db"

    uploads_dir: Path = Path("./data/uploads")
    generated_dir: Path = Path("./data/generated")
    topic_dictionary_path: Path = Path("./data/topics.json")
    task_keywords_path: Path = Path("./data/task_keywords.json")
    mock_users_path: Path = Path("./data/mock_users.json")

    bitrix_mode: str = Field(default="mock")
    bitrix_base_url: str = ""
    bitrix_webhook: str = ""

    autosave_enabled: bool = True
    topic_match_threshold: float = 0.34
    topic_required_as_error: bool = False

    cors_origins: str = "*"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache

def get_settings() -> Settings:
    settings = Settings()
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.generated_dir.mkdir(parents=True, exist_ok=True)
    settings.topic_dictionary_path.parent.mkdir(parents=True, exist_ok=True)
    return settings


settings = get_settings()
