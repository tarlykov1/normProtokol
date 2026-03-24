import { http } from './http'
import { mockApi } from '../lib/mockApi'
import { Protocol, ProtocolType, PublishResult, TaskCandidate, ValidationSummary } from '../../types/domain'

const isMock = import.meta.env.VITE_USE_MOCK_API === 'true'

function normalizeTask(task: TaskCandidate): TaskCandidate {
  const assignees = task.assignees_normalized ?? []
  const assigneesDisplay = task.assignees_display ?? (assignees.length ? assignees.join(', ') : task.assignee_b24_name ?? task.assignee_raw ?? null)
  return {
    ...task,
    warnings: task.warnings ?? [],
    errors: task.errors ?? [],
    markers: task.markers ?? [],
    assignees_normalized: assignees,
    assignees_display: assigneesDisplay,
    coordinator: task.coordinator ?? null,
    topic_candidate_list: task.topic_candidate_list ?? [],
    item_kind: task.item_kind ?? 'task',
    discussed_flag: task.discussed_flag ?? true,
    skipped_discussion_flag: task.skipped_discussion_flag ?? false
  }
}

function normalizeProtocol(protocol: Protocol): Protocol {
  return {
    ...protocol,
    tasks: (protocol.tasks ?? []).map((task) => normalizeTask(task as TaskCandidate)),
    topics: protocol.topics ?? []
  }
}

export const protocolsApi = {
  list: async () => {
    if (isMock) return mockApi.listProtocols()
    const data = (await http.get<Protocol[]>('/protocols')).data
    return data.map((protocol) => normalizeProtocol(protocol))
  },
  upload: async ({ file, protocolType }: { file: File; protocolType?: ProtocolType }) => {
    if (isMock) return mockApi.uploadProtocol()
    const fd = new FormData(); fd.append('file', file); fd.append('protocol_type', protocolType ?? 'auto')
    return normalizeProtocol((await http.post<Protocol>('/protocols/upload', fd)).data)
  },
  getById: async (id: number) => isMock ? mockApi.getProtocol() : normalizeProtocol((await http.get<Protocol>(`/protocols/${id}`)).data),
  getDraft: async (id: number) => isMock ? mockApi.getProtocol() : normalizeProtocol((await http.get<Protocol>(`/protocols/${id}/draft`)).data),
  saveDraft: async (id: number) => { if (isMock) return mockApi.saveDraft(); await http.post(`/protocols/${id}/save-draft`) },
  validate: async (id: number) => isMock ? mockApi.validate() : (await http.post<ValidationSummary>(`/protocols/${id}/validate`)).data,
  generateDocx: async (id: number) => { await http.post(`/protocols/${id}/generate-docx`) },
  downloadDocx: async (id: number) => (await http.get(`/protocols/${id}/download-docx`, { responseType: 'blob' })).data as Blob,
  publish: async (id: number) => isMock ? mockApi.publish() : (await http.post<PublishResult>(`/protocols/${id}/publish`)).data,
  demoBootstrap: async () => isMock ? mockApi.getProtocol() : normalizeProtocol((await http.post<Protocol>(`/demo/bootstrap`)).data)
}
