from app.services.normalizer.extractors.memo_meeting import MemoMeetingTaskExtractor


class MemoHierarchicalTaskExtractor(MemoMeetingTaskExtractor):
    protocol_type = "memo_hierarchical"
