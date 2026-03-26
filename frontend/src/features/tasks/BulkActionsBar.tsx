import { useState } from 'react'
import { Topic } from '../../types/domain'

export type BulkActionType = 'topic' | 'assignee' | 'deadline' | 'coordinator' | 'exclude' | 'delete'

interface Props {
  count: number
  topics: Topic[]
  pendingAction: BulkActionType | null
  onTopic: (topicId: number | null) => Promise<void>
  onDelete: () => Promise<void>
  onBulkUpdate: (action: Exclude<BulkActionType, 'topic' | 'delete'>, payload: { assignee_b24_name?: string | null; deadline_iso?: string | null; coordinator?: string | null; status?: string }) => Promise<void>
}

const actionButtonClass = 'rounded border px-2 py-1 transition-colors hover:bg-slate-100 active:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-60'

export function BulkActionsBar({ count, topics, pendingAction, onTopic, onDelete, onBulkUpdate }: Props) {
  const [assignee, setAssignee] = useState('')
  const [deadline, setDeadline] = useState('')
  const [coordinator, setCoordinator] = useState('')
  const isBusy = !!pendingAction
  const loadingLabel = pendingAction ? 'Выполняем действие…' : null

  if (!count) return null

  return (
    <div className="sticky top-0 z-10 mb-2 flex flex-wrap items-center gap-2 rounded border bg-white p-2 text-sm">
      <span>Выбрано: {count}</span>
      {loadingLabel && <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-700">{loadingLabel}</span>}
      <select
        className="w-full rounded border p-1 disabled:cursor-not-allowed disabled:bg-slate-100 sm:w-auto"
        disabled={isBusy}
        onChange={(e) => void onTopic(e.target.value ? Number(e.target.value) : null)}
      >
        <option value="">Назначить тему</option>
        {topics.map((t) => <option key={t.id} value={t.id}>{t.title}</option>)}
      </select>

      <input
        className="w-full rounded border p-1 disabled:cursor-not-allowed disabled:bg-slate-100 sm:w-64"
        placeholder="Массово: исполнитель"
        value={assignee}
        disabled={isBusy}
        onChange={(e) => setAssignee(e.target.value)}
      />
      <button
        onClick={() => void onBulkUpdate('assignee', { assignee_b24_name: assignee || null })}
        className={actionButtonClass}
        disabled={isBusy}
      >
        {pendingAction === 'assignee' ? 'Применяем...' : 'Применить исполнителя'}
      </button>

      <input
        type="date"
        className="w-full rounded border p-1 disabled:cursor-not-allowed disabled:bg-slate-100 sm:w-auto"
        value={deadline}
        disabled={isBusy}
        onChange={(e) => setDeadline(e.target.value)}
      />
      <button
        onClick={() => void onBulkUpdate('deadline', { deadline_iso: deadline || null })}
        className={actionButtonClass}
        disabled={isBusy}
      >
        {pendingAction === 'deadline' ? 'Применяем...' : 'Применить срок'}
      </button>
      <input
        className="w-full rounded border p-1 disabled:cursor-not-allowed disabled:bg-slate-100 sm:w-56"
        placeholder="Массово: координатор"
        value={coordinator}
        disabled={isBusy}
        onChange={(e) => setCoordinator(e.target.value)}
      />
      <button
        onClick={() => void onBulkUpdate('coordinator', { coordinator: coordinator || null })}
        className={actionButtonClass}
        disabled={isBusy}
      >
        {pendingAction === 'coordinator' ? 'Применяем...' : 'Применить координатора'}
      </button>

      <button
        onClick={() => void onBulkUpdate('exclude', { status: 'excluded' })}
        className={actionButtonClass}
        disabled={isBusy}
      >
        {pendingAction === 'exclude' ? 'Исключаем...' : 'Исключить из публикации'}
      </button>
      <button
        onClick={() => void onDelete()}
        className="rounded bg-red-600 px-2 py-1 text-white transition-colors hover:bg-red-700 active:bg-red-800 disabled:cursor-not-allowed disabled:bg-red-400"
        disabled={isBusy}
      >
        {pendingAction === 'delete' ? 'Удаляем...' : 'Удалить'}
      </button>
    </div>
  )
}
