import json

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.entities import Protocol, Topic


def seed_topics() -> None:
    db = SessionLocal()
    try:
        protocol = Protocol(original_filename="seed", original_file_path="seed", extracted_text="seed", status="seed")
        db.add(protocol)
        db.flush()
        with open(settings.topic_dictionary_path, "r", encoding="utf-8") as f:
            topics = json.load(f)
        for idx, t in enumerate(topics):
            db.add(Topic(protocol_id=protocol.id, title=t["title"], order_index=idx, source_type="auto", confidence=1.0, is_confirmed=True))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_topics()
