import { TaskCandidate, Topic } from '../../types/domain'
import { StatusBadge } from '../../shared/ui/StatusBadge'

interface Props {
  task: TaskCandidate
  topics: Topic[]
  selected: boolean
  onToggle: () => void
  onPatch: (id: number, patch: Record<string, unknown>) => void
}

export function TaskRow({ task, topics, selected, onToggle, onPatch }: Props) {
  const errors = task.errors ?? []
  const warnings = task.warnings ?? []
  const markers = task.markers ?? []
  const assignees = task.assignees_normalized ?? []

  const hasErrors = errors.length > 0 || task.status === 'needs_completion' || task.status === 'error'
  const hasWarnings = warnings.length > 0 || task.status === 'needs_review'
  const status = hasErrors ? 'error' : hasWarnings ? 'warning' : task.status === 'draft' ? 'draft' : 'ok'
  const assigneeHints = [...errors, ...warnings].filter((item) => {
    const lowered = item.toLowerCase()
    return lowered.includes('исполнител') || lowered.includes('bitrix24')
  })

  return (
    <tr className="border-b bg-white text-sm align-top">
      <td className="p-2"><input type="checkbox" checked={selected} onChange={onToggle} /></td>
      <td className="p-2">
        <select className="w-full rounded border p-1" value={task.topic_id ?? ''} onChange={(e) => onPatch(task.id, { topic_id: e.target.value ? Number(e.target.value) : null })}>
          <option value="">Без темы</option>{topics.map((t) => <option key={t.id} value={t.id}>{t.title}</option>)}
        </select>
        {(task.parent_context || task.context_label || task.section_name) && (
          <div className="mt-1 space-y-0.5 text-xs text-slate-600">
            {task.parent_context && <p><b>Контекст:</b> {task.parent_context}</p>}
            {task.context_label && <p><b>Источник:</b> {task.context_label}</p>}
            {task.section_name && <p><b>Секция:</b> {task.section_name}</p>}
          </div>
        )}
      </td>
      <td className="p-2">
        <textarea className="w-full rounded border p-1" rows={3} value={task.normalized_text} onChange={(e) => onPatch(task.id, { normalized_text: e.target.value })} />
        {markers.length > 0 && <p className="mt-1 text-xs text-slate-500">Маркеры: {markers.join(', ')}</p>}
      </td>
      <td className="p-2">
        <input className="w-full rounded border p-1" value={task.assignee_b24_name ?? task.assignee_raw ?? ''} onChange={(e) => onPatch(task.id, { assignee_b24_name: e.target.value })} />
        {assignees.length > 1 && <p className="mt-1 text-xs text-amber-700">Найдено несколько исполнителей: {assignees.join(', ')}</p>}
        {assigneeHints.length > 0 && <p className="mt-1 text-xs text-red-600">{assigneeHints.join('; ')}</p>}
      </td>
      <td className="p-2">
        <input type="date" className="w-full rounded border p-1" value={task.deadline_iso ?? ''} onChange={(e) => onPatch(task.id, { deadline_iso: e.target.value || null })} />
        <p className="mt-1 text-xs text-slate-600">{task.deadline_kind ?? 'без типа'}{task.deadline_note ? ` · ${task.deadline_note}` : ''}</p>
      </td>
      <td className="p-2">
        <StatusBadge status={status} />
        {(errors.length > 0 || warnings.length > 0) && (
          <div className="mt-1 space-y-1 text-xs">
            {errors.map((error, index) => <p key={`e-${index}`} className="text-red-700">• {error}</p>)}
            {warnings.map((warning, index) => <p key={`w-${index}`} className="text-amber-700">• {warning}</p>)}
          </div>
        )}
      </td>
      <td className="max-w-[300px] p-2 text-xs text-slate-600">
        <div className="min-h-[4.5rem] max-h-[4.5rem] overflow-y-auto whitespace-pre-wrap break-words" title={task.source_fragment}>
          {task.source_fragment}
        </div>
      </td>
    </tr>
  )
}
