import { http } from './http'

export const topicsApi = {
  create: async (protocolId: number, title: string) => { await http.post('/topics', { protocol_id: protocolId, title }) },
  patch: async (id: number, title: string) => { await http.patch(`/topics/${id}`, { title }) },
  remove: async (id: number) => { await http.delete(`/topics/${id}`) }
}
