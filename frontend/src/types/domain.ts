export type ProtocolStatus = 'uploaded' | 'parsed' | 'draft' | 'validated' | 'published' | 'error'

export interface Protocol {
  id: number
  original_filename: string
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
  deadline_raw: string | null
  deadline_iso: string | null
  status: string
  warnings: string[]
  errors: string[]
  order_index: number
  bitrix_task_id: string | null
}

export interface ValidationSummary {
  protocol_status_suggestion: string
  count_valid: number
  count_warnings: number
  count_errors: number
  task_results: Array<{ task_id: number; status: string; errors: string[]; warnings: string[] }>
}

export interface PublishResult {
  protocol_id: number
  smart_process_id: string
  published_tasks: Array<{ task_id: number; bitrix_task_id: string }>
  skipped_tasks: Array<{ task_id: number; reason: string }>
  errors: string[]
}

export interface Assignee {
  id: string
  name: string
}
