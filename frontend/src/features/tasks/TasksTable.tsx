import { TaskCandidate, Topic } from '../../types/domain'
import { TaskRow } from './TaskRow'

interface Props {
  tasks: TaskCandidate[]
  topics: Topic[]
  selectedIds: number[]
  onToggle: (id: number) => void
  onPatch: (id: number, patch: Record<string, unknown>) => void
}

export function TasksTable({ tasks, topics, selectedIds, onToggle, onPatch }: Props) {
  return (
    <div className="overflow-x-auto rounded border">
      <table className="min-w-full">
        <thead className="bg-slate-100 text-left text-xs uppercase">
          <tr><th className="p-2"/><th className="p-2">Тема и контекст</th><th className="p-2">Задача</th><th className="p-2">Исполнитель</th><th className="p-2">Срок</th><th className="p-2">Статус/причины</th><th className="p-2">Фрагмент</th></tr>
        </thead>
        <tbody>{tasks.map((task) => <TaskRow key={task.id} task={task} topics={topics} selected={selectedIds.includes(task.id)} onToggle={() => onToggle(task.id)} onPatch={onPatch} />)}</tbody>
      </table>
    </div>
  )
}
