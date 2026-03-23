from abc import ABC, abstractmethod


class BaseTaskExtractor(ABC):
    protocol_type = "standard"

    @abstractmethod
    def extract(
        self,
        chunks: list[str],
        topic_dictionary: list[dict],
        task_keywords: list[str],
        topic_threshold: float,
    ) -> list[dict]: ...
