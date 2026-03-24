export type ProtocolStatus =
  | 'uploaded'
  | 'parsed'
  | 'needs_review'
  | 'ready_to_publish'
  | 'published'
  | 'partially_published'
  | 'publish_error'

export type ProtocolType =
  | 'auto'
  | 'memo_meeting'
  | 'memo_preparation'
  | 'memo_mixed_sections'
  | 'memo_hierarchical'
  | 'simple'

export type TaskStatus =
  | 'draft'
  | 'extracted'
  | 'needs_review'
  | 'needs_completion'
  | 'needs_confirmation'
  | 'valid'
  | 'error'
  | 'excluded'
  | 'published'

export interface Protocol {
  id: number
  original_filename: string
  extracted_text?: string
  protocol_type: ProtocolType
  status: ProtocolStatus
  draft_saved_at: string | null
  normalized_docx_path: string | null
  published_docx_path: string | null
  bitrix_smart_process_id: string | null
  bitrix_publish_status: string | null
  topics: Topic[]
  tasks: TaskCandidate[]
}

export interface Topic {
  id: number
  protocol_id: number
  title: string
  order_index: number
  source_type: string
  confidence: number | null
  is_confirmed: boolean
}

export interface TaskCandidate {
  id: number
  protocol_id: number
  topic_id: number | null
  source_fragment: string
  normalized_text: string
  topic_auto_candidate: string | null
  topic_candidate_list: string[]
  assignee_raw: string | null
  assignee_b24_id: string | null
  assignee_b24_name: string | null
  assignees_raw: string | null
  assignees_normalized: string[]
  assignees_display: string | null
  coordinator: string | null
  deadline_raw: string | null
  deadline_iso: string | null
  deadline_kind: string | null
  deadline_note: string | null
  section_name: string | null
  parent_context: string | null
  context_label: string | null
  item_kind: 'agenda' | 'discussion' | 'task' | 'skipped_agenda'
  discussed_flag: boolean
  skipped_discussion_flag: boolean
  markers: string[]
  status: TaskStatus
  warnings: string[]
  errors: string[]
  order_index: number
  bitrix_task_id: string | null
}

export interface ValidationTaskResult {
  task_id: number
  errors: string[]
  warnings: string[]
}

export interface ValidationSummary {
  protocol_status_suggestion: ProtocolStatus
  count_valid: number
  count_warnings: number
  count_errors: number
  details: ValidationTaskResult[]
}

export interface SkippedTaskDetail {
  task_id: number
  normalized_text: string
  assignee_b24_name: string | null
  assignee_raw: string | null
  reason: string
  errors: string[]
  warnings: string[]
}

export interface PublishResult {
  protocol_id: number
  smart_process_id: string | null
  published_tasks: number[]
  skipped_tasks: number[]
  skipped_details: SkippedTaskDetail[]
  errors: string[]
}

export interface Assignee {
  id: string
  name: string
}
