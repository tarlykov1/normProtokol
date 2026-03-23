from app.services.normalizer.extractors.base import BaseTaskExtractor
from app.services.normalizer.task_extractor import extract_simple_task_candidates


class SimpleTaskExtractor(BaseTaskExtractor):
    protocol_type = "simple"

    def extract(self, chunks: list[str], topic_dictionary: list[dict], task_keywords: list[str], topic_threshold: float) -> list[dict]:
        return extract_simple_task_candidates(chunks, topic_dictionary, task_keywords, topic_threshold)
