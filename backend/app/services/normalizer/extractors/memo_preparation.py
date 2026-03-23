from app.services.normalizer.extractors.memo_meeting import MemoMeetingTaskExtractor


class MemoPreparationTaskExtractor(MemoMeetingTaskExtractor):
    protocol_type = "memo_preparation"
