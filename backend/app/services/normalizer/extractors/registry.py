from app.services.normalizer.extractors.base import BaseTaskExtractor
from app.services.normalizer.extractors.memo_hierarchical import MemoHierarchicalTaskExtractor
from app.services.normalizer.extractors.memo_meeting import MemoMeetingTaskExtractor
from app.services.normalizer.extractors.memo_mixed_sections import MemoMixedSectionsTaskExtractor
from app.services.normalizer.extractors.memo_preparation import MemoPreparationTaskExtractor
from app.services.normalizer.extractors.simple import SimpleTaskExtractor


class TaskExtractorRegistry:
    def __init__(self):
        self._extractors: dict[str, BaseTaskExtractor] = {}
        for extractor in [
            MemoMeetingTaskExtractor(),
            MemoPreparationTaskExtractor(),
            MemoMixedSectionsTaskExtractor(),
            MemoHierarchicalTaskExtractor(),
            SimpleTaskExtractor(),
        ]:
            self._extractors[extractor.protocol_type] = extractor

        # backward-compatible aliases for old protocol types
        self._extractors["standard"] = self._extractors["memo_meeting"]
        self._extractors["topics"] = self._extractors["memo_hierarchical"]
        self._extractors["blocks"] = self._extractors["memo_mixed_sections"]
        self._extractors["projects"] = self._extractors["memo_preparation"]

    def get(self, protocol_type: str | None) -> BaseTaskExtractor:
        key = (protocol_type or "memo_meeting").strip().lower()
        return self._extractors.get(key, self._extractors["memo_meeting"])
