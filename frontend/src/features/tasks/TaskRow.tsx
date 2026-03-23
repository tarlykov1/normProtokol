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
  const status = task.errors.length ? 'error' : task.warnings.length ? 'warning' : 'ok'
  const assigneeHints = [...task.errors, ...task.warnings].filter((item) => {
    const lowered = item.toLowerCase()
    return lowered.includes('исполнител') || lowered.includes('bitrix24')
  })

  return (
    <tr className="border-b bg-white text-sm">
      <td className="p-2"><input type="checkbox" checked={selected} onChange={onToggle} /></td>
      <td className="p-2"><select className="w-full rounded border p-1" value={task.topic_id ?? ''} onChange={(e) => onPatch(task.id, { topic_id: e.target.value ? Number(e.target.value) : null })}><option value="">Без темы</option>{topics.map((t) => <option key={t.id} value={t.id}>{t.title}</option>)}</select></td>
      <td className="p-2">
        <textarea
          className="w-full rounded border p-1"
          rows={3}
          value={task.normalized_text}
          onChange={(e) => onPatch(task.id, { normalized_text: e.target.value })}
        />
      </td>
      <td className="p-2">
        <input className="w-full rounded border p-1" value={task.assignee_b24_name ?? ''} onChange={(e) => onPatch(task.id, { assignee_b24_name: e.target.value })} />
        {assigneeHints.length > 0 && <p className="mt-1 text-xs text-red-600">{assigneeHints.join('; ')}</p>}
      </td>
      <td className="p-2"><input type="date" className="w-full rounded border p-1" value={task.deadline_iso ?? ''} onChange={(e) => onPatch(task.id, { deadline_iso: e.target.value || null })} /></td>
      <td className="p-2"><StatusBadge status={status} /></td>
      <td className="max-w-[300px] p-2 text-xs text-slate-600">
        <div className="min-h-[4.5rem] max-h-[4.5rem] overflow-y-auto whitespace-pre-wrap break-words" title={task.source_fragment}>
          {task.source_fragment}
        </div>
      </td>
    </tr>
  )
}
