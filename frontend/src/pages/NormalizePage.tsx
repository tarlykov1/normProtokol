import { useCallback, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useProtocolStore } from '../features/protocol/protocolStore'
import { useAutosaveDraft } from '../shared/hooks/useAutosaveDraft'
import { protocolsApi } from '../shared/api/protocolsApi'
import { tasksApi } from '../shared/api/tasksApi'
import { BulkActionType, BulkActionsBar } from '../features/tasks/BulkActionsBar'
import { TasksTable } from '../features/tasks/TasksTable'
import { useDeleteProtocol, usePatchTask, useProtocol } from '../features/protocol/useProtocolQueries'
import { EmptyState, ErrorState, LoadingState } from '../shared/ui/states'
import { ToastMessage, ToastStack } from '../shared/ui/ToastStack'

export function NormalizePage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const protocolId = Number(params.get('protocolId') || localStorage.getItem('lastProtocolId'))
  const { data, isLoading, error, refetch } = useProtocol(protocolId)
  const patch = usePatchTask(protocolId)
  const deleteProtocol = useDeleteProtocol()
  const { selectedTaskIds, toggleTask, clearSelection, filters, setFilters, setAutosaveState } = useProtocolStore()
  const [pendingBulkAction, setPendingBulkAction] = useState<BulkActionType | null>(null)
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  const pushToast = useCallback((payload: Omit<ToastMessage, 'id'>) => {
    setToasts((prev) => [...prev, { ...payload, id: Date.now() + Math.random() }])
  }, [])

  const dismissToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  const getErrorMessage = (error: unknown) => {
    if (error instanceof Error && error.message.trim()) return error.message
    return 'Попробуйте повторить позже или обратитесь к администратору.'
  }

  const showBulkResultToast = ({
    total,
    success,
    errorCount,
    errorMessage
  }: {
    total: number
    success: number
    errorCount: number
    errorMessage?: string
  }) => {
    if (errorCount > 0 && success > 0) {
      pushToast({
        kind: 'error',
        text: `Из ${total} задач обновлено ${success}, ${errorCount} — с ошибкой.`,
        detail: errorMessage
      })
      return
    }
    if (errorCount > 0) {
      pushToast({
        kind: 'error',
        text: 'Не удалось применить изменения',
        detail: errorMessage || 'Попробуйте повторить действие позже.'
      })
      return
    }
    pushToast({
      kind: 'success',
      text: total > 1 ? `Изменения применены (${success} из ${total})` : 'Изменения применены'
    })
  }

  useAutosaveDraft(!!data, async () => {
    if (!data) return
    try { setAutosaveState('saving'); await protocolsApi.saveDraft(data.id); setAutosaveState('saved') }
    catch { setAutosaveState('error') }
  })

  const filtered = useMemo(() => {
    if (!data) return []
    return data.tasks.filter((t) => {
      if (t.item_kind !== 'task') return false
      if (filters.noTopic && t.topic_id) return false
      if (filters.noAssignee && (t.assignees_display || t.assignee_b24_name || t.assignee_raw)) return false
      if (filters.noDeadline && t.deadline_iso) return false
      if (filters.onlyErrors && !t.errors.length) return false
      if (filters.onlyUnconfirmed && !['needs_confirmation','extracted','needs_review','needs_completion'].includes(t.status)) return false
      if (filters.onlyReady && t.status !== 'valid') return false
      if (filters.search && !t.normalized_text.toLowerCase().includes(filters.search.toLowerCase())) return false
      return true
    })
  }, [data, filters])

  if (!protocolId) return <EmptyState label="Сначала загрузите протокол." />
  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={(error as Error).message} />
  if (!data) return <EmptyState label="Протокол не найден" />

  const clearLastProtocolPointer = (deletedProtocolId: number) => {
    const savedLocalProtocolId = Number(localStorage.getItem('lastProtocolId'))
    if (savedLocalProtocolId === deletedProtocolId) {
      localStorage.removeItem('lastProtocolId')
    }
    const savedSessionProtocolId = Number(sessionStorage.getItem('lastProtocolId'))
    if (savedSessionProtocolId === deletedProtocolId) {
      sessionStorage.removeItem('lastProtocolId')
    }
  }

  const onDeleteProtocol = async () => {
    const shouldDelete = window.confirm(`Удалить протокол #${data.id} целиком?\nЭто удалит задачи, темы и связанные файлы.`)
    if (!shouldDelete) return
    await deleteProtocol.mutateAsync(data.id)
    clearLastProtocolPointer(data.id)
    navigate('/')
  }

  const runBulkAction = async (
    action: BulkActionType,
    operation: (selectedIds: number[]) => Promise<{ success: number; errorCount: number; errorMessage?: string }>
  ) => {
    if (pendingBulkAction || selectedTaskIds.length === 0) return
    const targetIds = [...selectedTaskIds]
    setPendingBulkAction(action)
    try {
      const result = await operation(targetIds)
      await refetch()
      if (result.errorCount === 0 && result.success > 0) {
        clearSelection()
      }
      showBulkResultToast({
        total: targetIds.length,
        success: result.success,
        errorCount: result.errorCount,
        errorMessage: result.errorMessage
      })
    } catch (error) {
      pushToast({
        kind: 'error',
        text: 'Не удалось применить изменения',
        detail: getErrorMessage(error)
      })
    } finally {
      setPendingBulkAction(null)
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-col gap-2 rounded border bg-white p-3 md:flex-row md:items-center md:justify-between">
        <div className="text-sm break-words">{data.original_filename} · тип: {data.protocol_type} · задач: {data.tasks.length}</div>
        <div className="flex w-full flex-wrap gap-2 md:w-auto md:flex-nowrap">
          <input className="w-full min-w-0 rounded border p-1 text-sm md:w-72" placeholder="Поиск..." value={filters.search} onChange={(e) => setFilters({ search: e.target.value })} />
          <button className="rounded border border-red-300 px-3 py-1 text-sm text-red-700" onClick={onDeleteProtocol} disabled={deleteProtocol.isPending}>
            {deleteProtocol.isPending ? 'Удаляем...' : 'Удалить протокол'}
          </button>
          <button className="rounded border px-3 py-1 text-sm" onClick={() => navigate(`/topics?protocolId=${data.id}`)}>Доска тем</button>
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
        pendingAction={pendingBulkAction}
        onTopic={async (topicId) => runBulkAction('topic', async (taskIds) => {
          const result = await tasksApi.bulkTopic(taskIds, topicId)
          const success = Math.min(result.count ?? 0, taskIds.length)
          return { success, errorCount: Math.max(taskIds.length - success, 0) }
        })}
        onBulkUpdate={async (action, payload) => runBulkAction(action, async (taskIds) => {
          const result = await tasksApi.bulkUpdate({ task_ids: taskIds, ...payload })
          const success = Math.min(result.count ?? 0, taskIds.length)
          return { success, errorCount: Math.max(taskIds.length - success, 0) }
        })}
        onDelete={async () => runBulkAction('delete', async (taskIds) => {
          const settled = await Promise.allSettled(taskIds.map((id) => tasksApi.remove(id)))
          const success = settled.filter((item) => item.status === 'fulfilled').length
          const firstError = settled.find((item) => item.status === 'rejected')
          const errorMessage = firstError && firstError.status === 'rejected'
            ? getErrorMessage(firstError.reason)
            : undefined
          return { success, errorCount: taskIds.length - success, errorMessage }
        })}
      />
      <TasksTable tasks={filtered} topics={data.topics} selectedIds={selectedTaskIds} onToggle={toggleTask} onPatch={(id, p) => patch.mutate({ id, patch: p })} />
      <ToastStack toasts={toasts} onClose={dismissToast} />
    </div>
  )
}
