from app.services.normalizer.extractors.standard import StandardTaskExtractor


class TopicsTaskExtractor(StandardTaskExtractor):
    protocol_type = "topics"
