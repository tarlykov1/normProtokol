import { Assignee, Protocol, PublishResult, ValidationSummary } from '../../types/domain'

const wait = (ms = 400) => new Promise((r) => setTimeout(r, ms))

let protocol: Protocol = {
  id: 1,
  original_filename: 'meeting.docx',
  protocol_type: 'standard',
  status: 'parsed',
  draft_saved_at: null,
  normalized_docx_path: null,
  published_docx_path: null,
  bitrix_smart_process_id: null,
  bitrix_publish_status: null,
  topics: [
    { id: 1, protocol_id: 1, title: 'Продажи', order_index: 1, source_type: 'auto', confidence: 0.8, is_confirmed: true },
    { id: 2, protocol_id: 1, title: 'Продукт', order_index: 2, source_type: 'auto', confidence: 0.7, is_confirmed: true }
  ],
  tasks: [
    { id: 11, protocol_id: 1, topic_id: 1, source_fragment: 'Сделать КП до пятницы', normalized_text: 'Подготовить КП для клиента A', topic_auto_candidate: 'Продажи', topic_candidate_list: ['Продажи'], assignee_raw: 'Иван', assignee_b24_id: '101', assignee_b24_name: 'Иван Петров', deadline_raw: 'пятница', deadline_iso: '2026-03-27', status: 'draft', warnings: [], errors: [], order_index: 1, bitrix_task_id: null },
    { id: 12, protocol_id: 1, topic_id: null, source_fragment: 'Проверить onboarding', normalized_text: 'Обновить чеклист onboarding', topic_auto_candidate: null, topic_candidate_list: [], assignee_raw: null, assignee_b24_id: null, assignee_b24_name: null, deadline_raw: null, deadline_iso: null, status: 'draft', warnings: ['Нет исполнителя'], errors: [], order_index: 2, bitrix_task_id: null }
  ]
}

export const mockApi = {
  async listProtocols(): Promise<Protocol[]> { await wait(); return [protocol] },
  async uploadProtocol(): Promise<Protocol> { await wait(); return protocol },
  async getProtocol(): Promise<Protocol> { await wait(); return protocol },
  async patchTask(id: number, patch: Partial<Protocol['tasks'][number]>): Promise<void> { await wait(150); protocol = { ...protocol, tasks: protocol.tasks.map((t) => t.id === id ? { ...t, ...patch } : t) } },
  async saveDraft(): Promise<void> { await wait(200); protocol = { ...protocol, draft_saved_at: new Date().toISOString() } },
  async validate(): Promise<ValidationSummary> {
    await wait()
    return {
      protocol_status_suggestion: 'ready_to_publish',
      count_valid: 1,
      count_warnings: 1,
      count_errors: 0,
      details: protocol.tasks.map((t) => ({ task_id: t.id, errors: t.errors, warnings: t.warnings }))
    }
  },
  async publish(): Promise<PublishResult> {
    await wait()
    return {
      protocol_id: 1,
      smart_process_id: 'SP-777',
      published_tasks: [11],
      skipped_tasks: [12],
      skipped_details: [
        {
          task_id: 12,
          normalized_text: 'Обновить чеклист onboarding',
          assignee_b24_name: null,
          assignee_raw: null,
          reason: 'Не найден исполнитель в Bitrix24',
          errors: ['Исполнитель не найден в Bitrix24. Выберите другого исполнителя или отправьте заявку.'],
          warnings: []
        }
      ],
      errors: []
    }
  },
  async searchAssignee(q: string): Promise<Assignee[]> { await wait(100); return [{ id: '101', name: 'Иван Петров' }, { id: '102', name: 'Мария Смирнова' }].filter((x) => x.name.toLowerCase().includes(q.toLowerCase())) }
}
