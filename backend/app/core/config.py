from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Protocol Normalizer"
    debug: bool = True
    api_prefix: str = "/api"

    database_url: str = "sqlite:///./data/app.db"

    storage_root: Path = Path("./data")
    uploads_dir: Path = Path("./data/uploads")
    exports_dir: Path = Path("./data/exports")
    drafts_dir: Path = Path("./data/drafts")

    topic_dictionary_path: Path = Path("./backend/app/data/topics.json")

    bitrix_mock_mode: bool = True
    bitrix_webhook_url: str = ""
    bitrix_smart_process_entity_type_id: int = 0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
for directory in (settings.storage_root, settings.uploads_dir, settings.exports_dir, settings.drafts_dir):
    directory.mkdir(parents=True, exist_ok=True)
