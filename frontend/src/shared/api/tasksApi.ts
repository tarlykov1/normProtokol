import { http } from './http'

export const tasksApi = {
  patch: async (id: number, patch: Record<string, unknown>) => { await http.patch(`/tasks/${id}`, patch) },
  create: async (payload: Record<string, unknown>) => { await http.post('/tasks', payload) },
  remove: async (id: number) => { await http.delete(`/tasks/${id}`) },
  split: async (id: number, splitIndex: number) => { await http.post(`/tasks/${id}/split`, { split_index: splitIndex }) },
  merge: async (taskIds: number[]) => { await http.post('/tasks/merge', { task_ids: taskIds }) },
  moveToTopic: async (taskIds: number[], topic_id: number | null) => { await http.post('/tasks/move-to-topic', { task_ids: taskIds, topic_id }) },
  reorder: async (taskOrders: Array<{ task_id: number; order_index: number }>) => { await http.post('/tasks/reorder', { task_orders: taskOrders }) },
  bulkTopic: async (taskIds: number[], topic_id: number | null) => { await http.post('/topics/bulk-assign', { task_ids: taskIds, topic_id }) }
}
