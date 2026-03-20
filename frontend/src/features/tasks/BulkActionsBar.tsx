import { Topic } from '../../types/domain'

interface Props {
  count: number
  topics: Topic[]
  onTopic: (topicId: number | null) => void
  onDelete: () => void
}

export function BulkActionsBar({ count, topics, onTopic, onDelete }: Props) {
  if (!count) return null
  return (
    <div className="sticky top-0 z-10 mb-2 flex items-center gap-2 rounded border bg-white p-2 text-sm">
      <span>Выбрано: {count}</span>
      <select className="rounded border p-1" onChange={(e) => onTopic(e.target.value ? Number(e.target.value) : null)}>
        <option value="">Назначить тему</option>
        {topics.map((t) => <option key={t.id} value={t.id}>{t.title}</option>)}
      </select>
      <button onClick={onDelete} className="rounded bg-red-600 px-2 py-1 text-white">Удалить</button>
    </div>
  )
}
