export type Topic = {
  id: number
  protocol_id: number
  title: string
  order_index: number
  source_type: string
  confidence: number
  is_confirmed: boolean
}

export type Task = {
  id: number
  protocol_id: number
  topic_id: number | null
  source_fragment: string
  normalized_text: string
  assignee_b24_id: string | null
  assignee_b24_name: string | null
  deadline_iso: string | null
  status: string
  warnings: string[]
  errors: string[]
  order_index: number
}

export type Protocol = {
  id: number
  original_filename: string
  status: string
  extracted_text: string
  draft_saved_at: string | null
  normalized_docx_path: string | null
  bitrix_smart_process_id: string | null
  bitrix_publish_status: string | null
  topics: Topic[]
  tasks: Task[]
}
