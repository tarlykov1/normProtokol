import { DndContext, DragEndEvent, useDraggable, useDroppable } from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'
import { TaskCandidate, Topic } from '../../types/domain'

function Card({ task }: { task: TaskCandidate }) {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({ id: `task-${task.id}` })
  return <div ref={setNodeRef} style={{ transform: CSS.Translate.toString(transform) }} {...listeners} {...attributes} className="mb-2 rounded border bg-white p-2 text-sm">{task.normalized_text}</div>
}

function Column({ topic, tasks }: { topic: Topic | null; tasks: TaskCandidate[] }) {
  const key = topic ? `topic-${topic.id}` : 'topic-null'
  const { setNodeRef, isOver } = useDroppable({ id: key })
  return (
    <section ref={setNodeRef} className={`min-w-[260px] flex-1 rounded border p-2 ${isOver ? 'bg-green-50' : 'bg-slate-50'}`}>
      <h4 className="mb-2 text-sm font-semibold">{topic?.title ?? 'Без темы'}</h4>
      {tasks.map((t) => <Card key={t.id} task={t} />)}
    </section>
  )
}

export function TopicsBoard({ topics, tasks, onDrop }: { topics: Topic[]; tasks: TaskCandidate[]; onDrop: (taskId: number, topicId: number | null) => void }) {
  const groups = topics.map((topic) => ({ topic, tasks: tasks.filter((t) => t.topic_id === topic.id).sort((a, b) => a.order_index - b.order_index) }))
  const unassigned = tasks.filter((t) => !t.topic_id)

  const onDragEnd = (e: DragEndEvent) => {
    if (!e.over) return
    const taskId = Number(String(e.active.id).replace('task-', ''))
    const topicId = e.over.id === 'topic-null' ? null : Number(String(e.over.id).replace('topic-', ''))
    onDrop(taskId, topicId)
  }

  return (
    <DndContext onDragEnd={onDragEnd}>
      <div className="flex gap-3 overflow-x-auto">
        {groups.map((g) => <Column key={g.topic.id} topic={g.topic} tasks={g.tasks} />)}
        <Column topic={null} tasks={unassigned} />
      </div>
    </DndContext>
  )
}
