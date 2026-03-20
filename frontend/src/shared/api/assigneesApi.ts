import { Assignee } from '../../types/domain'
import { http } from './http'
import { mockApi } from '../lib/mockApi'

const isMock = import.meta.env.VITE_USE_MOCK_API === 'true'

export const assigneesApi = {
  search: async (q: string) => isMock ? mockApi.searchAssignee(q) : (await http.get<Assignee[]>(`/assignees/search?q=${encodeURIComponent(q)}`)).data
}
