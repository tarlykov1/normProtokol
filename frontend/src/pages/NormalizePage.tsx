import { useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useProtocolStore } from '../features/protocol/protocolStore'
import { useAutosaveDraft } from '../shared/hooks/useAutosaveDraft'
import { protocolsApi } from '../shared/api/protocolsApi'
import { tasksApi } from '../shared/api/tasksApi'
import { BulkActionsBar } from '../features/tasks/BulkActionsBar'
import { TasksTable } from '../features/tasks/TasksTable'
import { usePatchTask, useProtocol } from '../features/protocol/useProtocolQueries'
import { EmptyState, ErrorState, LoadingState } from '../shared/ui/states'

export function NormalizePage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const protocolId = Number(params.get('protocolId') || localStorage.getItem('lastProtocolId'))
  const { data, isLoading, error, refetch } = useProtocol(protocolId)
  const patch = usePatchTask(protocolId)
  const { selectedTaskIds, toggleTask, clearSelection, filters, setFilters, setAutosaveState } = useProtocolStore()

  useAutosaveDraft(!!data, async () => {
    if (!data) return
    try { setAutosaveState('saving'); await protocolsApi.saveDraft(data.id); setAutosaveState('saved') }
    catch { setAutosaveState('error') }
  })

  const filtered = useMemo(() => {
    if (!data) return []
    return data.tasks.filter((t) => {
      if (filters.noTopic && t.topic_id) return false
      if (filters.noAssignee && t.assignee_b24_name) return false
      if (filters.noDeadline && t.deadline_iso) return false
      if (filters.onlyErrors && !t.errors.length) return false
      if (filters.onlyUnconfirmed && t.status !== 'needs_confirmation') return false
      if (filters.onlyReady && t.status !== 'valid') return false
      if (filters.search && !t.normalized_text.toLowerCase().includes(filters.search.toLowerCase())) return false
      return true
    })
  }, [data, filters])

  if (!protocolId) return <EmptyState label="Сначала загрузите протокол." />
  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={(error as Error).message} />
  if (!data) return <EmptyState label="Протокол не найден" />

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between rounded border bg-white p-3">
        <div className="text-sm">{data.original_filename} · задач: {data.tasks.length}</div>
        <div className="flex gap-2">
          <input className="rounded border p-1 text-sm" placeholder="Поиск..." value={filters.search} onChange={(e) => setFilters({ search: e.target.value })} />
          <button className="rounded border px-3 py-1 text-sm" onClick={() => navigate(`/topics?protocolId=${data.id}`)}>Board view</button>
          <button className="rounded bg-slate-900 px-3 py-1 text-sm text-white" onClick={() => navigate(`/confirm?protocolId=${data.id}`)}>К подтверждению</button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 rounded border bg-white p-2 text-xs">
        <label><input type="checkbox" checked={filters.noTopic} onChange={(e) => setFilters({ noTopic: e.target.checked })} /> Без темы</label>
        <label><input type="checkbox" checked={filters.noAssignee} onChange={(e) => setFilters({ noAssignee: e.target.checked })} /> Без исполнителя</label>
        <label><input type="checkbox" checked={filters.noDeadline} onChange={(e) => setFilters({ noDeadline: e.target.checked })} /> Без срока</label>
        <label><input type="checkbox" checked={filters.onlyErrors} onChange={(e) => setFilters({ onlyErrors: e.target.checked })} /> Только ошибки</label>
        <label><input type="checkbox" checked={filters.onlyUnconfirmed} onChange={(e) => setFilters({ onlyUnconfirmed: e.target.checked })} /> Неподтвержденные</label>
        <label><input type="checkbox" checked={filters.onlyReady} onChange={(e) => setFilters({ onlyReady: e.target.checked })} /> Готовые к публикации</label>
      </div>

      <BulkActionsBar
        count={selectedTaskIds.length}
        topics={data.topics}
        onTopic={async (topicId) => { await tasksApi.bulkTopic(selectedTaskIds, topicId); clearSelection(); await refetch() }}
        onBulkUpdate={async (payload) => { await tasksApi.bulkUpdate({ task_ids: selectedTaskIds, ...payload }); await refetch() }}
        onDelete={async () => { await Promise.all(selectedTaskIds.map((id) => tasksApi.remove(id))); clearSelection(); await refetch() }}
      />
      <TasksTable tasks={filtered} topics={data.topics} selectedIds={selectedTaskIds} onToggle={toggleTask} onPatch={(id, p) => patch.mutate({ id, patch: p })} />
    </div>
  )
}
