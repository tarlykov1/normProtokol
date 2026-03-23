from app.services.normalizer.extractors.standard import StandardTaskExtractor


class BlocksTaskExtractor(StandardTaskExtractor):
    protocol_type = "blocks"
