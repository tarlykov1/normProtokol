import { useMemo, useState } from 'react'
import { TaskCandidate, Topic } from '../../types/domain'
import { StatusBadge } from '../../shared/ui/StatusBadge'
import { cn } from '../../shared/lib/cn'

interface Props {
  task: TaskCandidate
  topics: Topic[]
  selected: boolean
  onToggle: () => void
  onPatch: (id: number, patch: Record<string, unknown>) => void
}

export function TaskRow({ task, topics, selected, onToggle, onPatch }: Props) {
  const [fragmentExpanded, setFragmentExpanded] = useState(false)
  const errors = task.errors ?? []
  const warnings = task.warnings ?? []
  const markers = task.markers ?? []

  const hasErrors = errors.length > 0 || task.status === 'needs_completion' || task.status === 'error'
  const hasWarnings = warnings.length > 0 || task.status === 'needs_review'
  const status = hasErrors ? 'error' : hasWarnings ? 'warning' : task.status === 'draft' ? 'draft' : 'ok'

  const statusMessages = useMemo(() => {
    const allMessages = [...errors, ...warnings]
    const normalized = allMessages
      .map((message) => message.replace(/\s+/g, ' ').trim())
      .filter(Boolean)
      .map((message) => {
        const lowered = message.toLowerCase()
        if (/(traceback|stack|sql|exception|http|timeout|failed|invalid|cannot)/.test(lowered)) {
          if (lowered.includes('срок')) return 'Не указан срок'
          if (lowered.includes('исполн')) return 'Проблема с исполнителем'
          return 'Требуется уточнение данных'
        }
        if (lowered.includes('не указан срок')) return 'Не указан срок'
        return message
      })
    return Array.from(new Set(normalized))
  }, [errors, warnings])

  const assigneesDisplay = useMemo(() => {
    if (task.assignees_display?.trim()) return task.assignees_display
    if ((task.assignees_normalized ?? []).length) return task.assignees_normalized.join(', ')
    return task.assignee_b24_name ?? task.assignee_raw ?? ''
  }, [task.assignees_display, task.assignees_normalized, task.assignee_b24_name, task.assignee_raw])

  const deadlineDisplay = task.deadline_iso ?? task.deadline_raw ?? task.deadline_note ?? ''

  return (
    <tr className="border-b bg-white text-sm align-top">
      <td className="p-2"><input type="checkbox" checked={selected} onChange={onToggle} /></td>
      <td className="p-2">
        <div className="space-y-1">
          <select className="w-full rounded border p-1" value={task.topic_id ?? ''} onChange={(e) => onPatch(task.id, { topic_id: e.target.value ? Number(e.target.value) : null })}>
            <option value="">Без темы</option>{topics.map((t) => <option key={t.id} value={t.id}>{t.title}</option>)}
          </select>
          <StatusBadge status={status} messages={statusMessages} />
        </div>
      </td>

      <td className="p-2">
        <textarea className="w-full rounded border p-1" rows={2} value={task.normalized_text} onChange={(e) => onPatch(task.id, { normalized_text: e.target.value })} />
        <div className="mt-1 rounded border bg-slate-50 p-2 text-xs text-slate-700">
          <div className="mb-1 flex items-center justify-between gap-2">
            <span className="font-medium">Фрагмент из файла</span>
            <button className="rounded border px-2 py-0.5 text-[11px]" onClick={() => setFragmentExpanded((v) => !v)}>
              {fragmentExpanded ? 'Свернуть' : 'Развернуть'}
            </button>
          </div>
          <div className={cn('whitespace-pre-wrap break-words', fragmentExpanded ? 'max-h-60 overflow-y-auto' : 'max-h-12 overflow-hidden')} title={task.source_fragment}>
            {task.source_fragment}
          </div>
        </div>
        {markers.length > 0 && <p className="mt-1 text-xs text-slate-500">Маркеры: {markers.join(', ')}</p>}
      </td>

      <td className="p-2">
        <div className="space-y-2">
          <div>
            <input type="date" className="w-full rounded border p-1" value={task.deadline_iso ?? ''} onChange={(e) => onPatch(task.id, { deadline_iso: e.target.value || null })} />
            {!!deadlineDisplay && !task.deadline_iso && <p className="mt-1 text-xs text-slate-600">{deadlineDisplay}</p>}
          </div>
          <div>
            <input className="w-full rounded border p-1" value={assigneesDisplay} onChange={(e) => onPatch(task.id, { assignees_display: e.target.value, assignee_b24_name: e.target.value })} placeholder="Исполнители через запятую" />
          </div>
          <div>
            <input className="w-full rounded border p-1" value={task.coordinator ?? ''} onChange={(e) => onPatch(task.id, { coordinator: e.target.value || null })} placeholder="Координатор (необязательно)" />
          </div>
        </div>
      </td>
    </tr>
  )
}
