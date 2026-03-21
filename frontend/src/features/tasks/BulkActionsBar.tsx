import { useState } from 'react'
import { Topic } from '../../types/domain'

interface Props {
  count: number
  topics: Topic[]
  onTopic: (topicId: number | null) => void
  onDelete: () => void
  onBulkUpdate: (payload: { assignee_b24_name?: string | null; deadline_iso?: string | null; status?: string }) => void
}

export function BulkActionsBar({ count, topics, onTopic, onDelete, onBulkUpdate }: Props) {
  const [assignee, setAssignee] = useState('')
  const [deadline, setDeadline] = useState('')

  if (!count) return null

  return (
    <div className="sticky top-0 z-10 mb-2 flex flex-wrap items-center gap-2 rounded border bg-white p-2 text-sm">
      <span>Выбрано: {count}</span>
      <select className="rounded border p-1" onChange={(e) => onTopic(e.target.value ? Number(e.target.value) : null)}>
        <option value="">Назначить тему</option>
        {topics.map((t) => <option key={t.id} value={t.id}>{t.title}</option>)}
      </select>

      <input
        className="rounded border p-1"
        placeholder="Массово: исполнитель"
        value={assignee}
        onChange={(e) => setAssignee(e.target.value)}
      />
      <button
        onClick={() => onBulkUpdate({ assignee_b24_name: assignee || null })}
        className="rounded border px-2 py-1"
      >
        Применить исполнителя
      </button>

      <input type="date" className="rounded border p-1" value={deadline} onChange={(e) => setDeadline(e.target.value)} />
      <button
        onClick={() => onBulkUpdate({ deadline_iso: deadline || null })}
        className="rounded border px-2 py-1"
      >
        Применить срок
      </button>

      <button onClick={() => onBulkUpdate({ status: 'excluded' })} className="rounded border px-2 py-1">Исключить из публикации</button>
      <button onClick={onDelete} className="rounded bg-red-600 px-2 py-1 text-white">Удалить</button>
    </div>
  )
}
