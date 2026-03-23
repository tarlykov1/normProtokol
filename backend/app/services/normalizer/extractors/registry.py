from app.services.normalizer.extractors.base import BaseTaskExtractor
from app.services.normalizer.extractors.blocks import BlocksTaskExtractor
from app.services.normalizer.extractors.projects import ProjectsTaskExtractor
from app.services.normalizer.extractors.simple import SimpleTaskExtractor
from app.services.normalizer.extractors.standard import StandardTaskExtractor
from app.services.normalizer.extractors.topics import TopicsTaskExtractor


class TaskExtractorRegistry:
    def __init__(self):
        self._extractors: dict[str, BaseTaskExtractor] = {}
        for extractor in [
            StandardTaskExtractor(),
            TopicsTaskExtractor(),
            BlocksTaskExtractor(),
            ProjectsTaskExtractor(),
            SimpleTaskExtractor(),
        ]:
            self._extractors[extractor.protocol_type] = extractor

    def get(self, protocol_type: str | None) -> BaseTaskExtractor:
        key = (protocol_type or "standard").strip().lower()
        return self._extractors.get(key, self._extractors["standard"])
