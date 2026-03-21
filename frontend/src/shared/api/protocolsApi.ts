import { http } from './http'
import { mockApi } from '../lib/mockApi'
import { Protocol, PublishResult, ValidationSummary } from '../../types/domain'

const isMock = import.meta.env.VITE_USE_MOCK_API === 'true'

export const protocolsApi = {
  list: async () => isMock ? mockApi.listProtocols() : (await http.get<Protocol[]>('/protocols')).data,
  upload: async (file: File) => {
    if (isMock) return mockApi.uploadProtocol()
    const fd = new FormData(); fd.append('file', file)
    return (await http.post<Protocol>('/protocols/upload', fd)).data
  },
  getById: async (id: number) => isMock ? mockApi.getProtocol() : (await http.get<Protocol>(`/protocols/${id}`)).data,
  getDraft: async (id: number) => isMock ? mockApi.getProtocol() : (await http.get<Protocol>(`/protocols/${id}/draft`)).data,
  saveDraft: async (id: number) => { if (isMock) return mockApi.saveDraft(); await http.post(`/protocols/${id}/save-draft`) },
  validate: async (id: number) => isMock ? mockApi.validate() : (await http.post<ValidationSummary>(`/protocols/${id}/validate`)).data,
  generateDocx: async (id: number) => { await http.post(`/protocols/${id}/generate-docx`) },
  downloadDocx: async (id: number) => (await http.get(`/protocols/${id}/download-docx`, { responseType: 'blob' })).data as Blob,
  publish: async (id: number) => isMock ? mockApi.publish() : (await http.post<PublishResult>(`/protocols/${id}/publish`)).data,
  demoBootstrap: async () => isMock ? mockApi.getProtocol() : (await http.post<Protocol>(`/demo/bootstrap`)).data
}
