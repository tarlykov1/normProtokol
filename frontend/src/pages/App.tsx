import { useEffect, useMemo, useState } from 'react'
import { DndContext, DragEndEvent, useDraggable, useDroppable } from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'
import { api } from '../api/client'
import { Protocol, Task, Topic } from '../types'

const steps = ['Upload', 'Нормализация', 'Группировка', 'Подтверждение', 'Результат']

function DraggableTask({ task }: { task: Task }) {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({ id: `task-${task.id}` })
  const style = { transform: CSS.Translate.toString(transform) }
  return (
    <div ref={setNodeRef} style={style} {...listeners} {...attributes} className="task-item">
      {task.normalized_text}
    </div>
  )
}

function TopicColumn({ topic, tasks }: { topic: Topic | null; tasks: Task[] }) {
  const id = topic ? `topic-${topic.id}` : 'topic-unassigned'
  const { setNodeRef, isOver } = useDroppable({ id })
  return (
    <div ref={setNodeRef} id={id} className="topic-col" style={{ background: isOver ? '#e8f5e9' : '#fafafa' }}>
      <h4>{topic?.title ?? 'Без темы'}</h4>
      {tasks.map((task) => (
        <DraggableTask key={task.id} task={task} />
      ))}
    </div>
  )
}

export function App() {
  const [step, setStep] = useState(0)
  const [protocol, setProtocol] = useState<Protocol | null>(null)
  const [selectedTaskIds, setSelectedTaskIds] = useState<number[]>([])
  const [publishReport, setPublishReport] = useState<any>(null)

  useEffect(() => {
    const saved = localStorage.getItem('lastProtocolId')
    if (saved) {
      api.get(`/protocols/${saved}/draft`).then(r => setProtocol(r.data)).catch(() => undefined)
    }
  }, [])

  useEffect(() => {
    if (!protocol) return
    const timer = setInterval(() => {
      api.post(`/protocols/${protocol.id}/save-draft`).catch(() => undefined)
    }, 10000)
    return () => clearInterval(timer)
  }, [protocol])

  const tasksByTopic = useMemo(() => {
    const map: Record<string, Task[]> = { unassigned: [] }
    if (!protocol) return map
    for (const topic of protocol.topics) map[String(topic.id)] = []
    protocol.tasks.forEach(t => {
      if (t.topic_id && map[String(t.topic_id)]) map[String(t.topic_id)].push(t)
      else map.unassigned.push(t)
    })
    return map
  }, [protocol])

  const refreshProtocol = async () => {
    if (!protocol) return
    const { data } = await api.get(`/protocols/${protocol.id}`)
    setProtocol(data)
  }

  const upload = async (file: File) => {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post('/protocols/upload', form)
    setProtocol(data)
    localStorage.setItem('lastProtocolId', String(data.id))
    setStep(1)
  }

  const updateTask = async (taskId: number, patch: any) => {
    await api.patch(`/tasks/${taskId}`, patch)
    await refreshProtocol()
  }

  const bulkAssign = async (topicId: number | null) => {
    if (!selectedTaskIds.length || !topicId) return
    await api.post('/tasks/bulk-topic', { task_ids: selectedTaskIds, topic_id: topicId })
    await refreshProtocol()
  }

  const onDragEnd = async (e: DragEndEvent) => {
    if (!e.over) return
    const taskId = Number(String(e.active.id).replace('task-', ''))
    const target = String(e.over.id)
    const targetTopic = target === 'topic-unassigned' ? null : Number(target.replace('topic-', ''))
    await api.post('/tasks/move-to-topic', { task_ids: [taskId], topic_id: targetTopic })
    await refreshProtocol()
  }

  const generateDoc = async () => {
    if (!protocol) return
    await api.post(`/protocols/${protocol.id}/generate-docx`)
    await refreshProtocol()
  }

  const publish = async () => {
    if (!protocol) return
    await api.post(`/protocols/${protocol.id}/validate`)
    const { data } = await api.post(`/protocols/${protocol.id}/publish`)
    setPublishReport(data)
    await refreshProtocol()
    setStep(4)
  }

  return (
    <div className="container">
      <h2>Protocol Normalizer MVP</h2>
      <p>{steps.map((s, i) => `${i === step ? '➡️' : '•'} ${s}`).join('   ')}</p>

      {step === 0 && <div className="card"><input type="file" accept=".docx" onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} /></div>}

      {step === 1 && protocol && (
        <div className="card">
          <h3>Нормализация</h3>
          <button onClick={() => setStep(2)}>К группировке</button>
          <button onClick={() => api.post(`/protocols/${protocol.id}/save-draft`)}>Сохранить черновик</button>
          <table>
            <thead><tr><th>#</th><th>Тема</th><th>Текст</th><th>Исполнитель</th><th>Срок</th><th>Статус</th><th>Фрагмент</th></tr></thead>
            <tbody>
              {protocol.tasks.map((task) => (
                <tr key={task.id}>
                  <td><input type="checkbox" checked={selectedTaskIds.includes(task.id)} onChange={(e) => setSelectedTaskIds(p => e.target.checked ? [...p, task.id] : p.filter(x => x !== task.id))} /> {task.id}</td>
                  <td><select value={task.topic_id ?? ''} onChange={(e) => updateTask(task.id, { topic_id: Number(e.target.value) || null })}><option value="">--</option>{protocol.topics.map(t => <option key={t.id} value={t.id}>{t.title}</option>)}</select></td>
                  <td><textarea value={task.normalized_text} onChange={(e) => updateTask(task.id, { normalized_text: e.target.value })} /></td>
                  <td><input value={task.assignee_b24_name ?? ''} onChange={(e) => updateTask(task.id, { assignee_b24_name: e.target.value })} /></td>
                  <td><input value={task.deadline_iso ?? ''} onChange={(e) => updateTask(task.id, { deadline_iso: e.target.value })} /></td>
                  <td className={task.errors.length ? 'status-error' : task.warnings.length ? 'status-warning' : 'status-ok'}>{task.errors.length ? 'error' : task.warnings.length ? 'warning' : 'ok'}</td>
                  <td>{task.source_fragment}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: 12 }}>
            <select onChange={e => bulkAssign(Number(e.target.value))}><option value="">Массово назначить тему...</option>{protocol.topics.map((t) => <option key={t.id} value={t.id}>{t.title}</option>)}</select>
          </div>
        </div>
      )}

      {step === 2 && protocol && (
        <div className="card">
          <h3>Группировка по темам (drag-and-drop)</h3>
          <button onClick={() => setStep(1)}>Назад</button>
          <button onClick={() => setStep(3)}>К подтверждению</button>
          <DndContext onDragEnd={onDragEnd}>
            <div className="flex">
              {protocol.topics.map((topic: Topic) => <TopicColumn key={topic.id} topic={topic} tasks={tasksByTopic[String(topic.id)] ?? []} />)}
              <TopicColumn topic={null} tasks={tasksByTopic.unassigned ?? []} />
            </div>
          </DndContext>
        </div>
      )}

      {step === 3 && protocol && (
        <div className="card">
          <h3>Подтверждение</h3>
          <p>Задач: {protocol.tasks.length}, Тем: {protocol.topics.length}</p>
          <button onClick={() => api.post(`/protocols/${protocol.id}/save-draft`)}>Сохранить черновик</button>
          <button onClick={generateDoc}>Сформировать Word</button>
          <button onClick={() => window.open(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'}/protocols/${protocol.id}/download-docx`, '_blank')}>Скачать Word</button>
          <button onClick={publish}>Отправить в Bitrix24</button>
        </div>
      )}

      {step === 4 && protocol && <div className="card"><h3>Результат</h3><pre>{JSON.stringify(publishReport, null, 2)}</pre></div>}
    </div>
  )
}
