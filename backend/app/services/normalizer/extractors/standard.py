from app.services.normalizer.extractors.base import BaseTaskExtractor
from app.services.normalizer.task_extractor import extract_task_candidates


class StandardTaskExtractor(BaseTaskExtractor):
    protocol_type = "standard"

    def extract(self, chunks: list[str], topic_dictionary: list[dict], task_keywords: list[str], topic_threshold: float) -> list[dict]:
        return extract_task_candidates(chunks, topic_dictionary, task_keywords, topic_threshold)
