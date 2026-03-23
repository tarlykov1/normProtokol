import { useLocation, useNavigate } from 'react-router-dom'
import { PublishResult } from '../types/domain'

export function ResultPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const result = location.state as PublishResult | undefined

  if (!result) return <div className="rounded border bg-white p-4">Нет данных публикации.</div>

  return (
    <div className="space-y-3 rounded border bg-white p-4">
      <h2 className="text-lg font-semibold">Результат публикации</h2>
      <p className="text-sm">ID смарт-процесса: {result.smart_process_id}</p>
      <p className="text-sm">Опубликовано: {result.published_tasks.length}, пропущено: {result.skipped_tasks.length}</p>
      {result.errors.length > 0 && <pre className="rounded bg-red-50 p-2 text-xs text-red-700">{JSON.stringify(result.errors, null, 2)}</pre>}
      <div className="flex gap-2">
        <button className="rounded border px-3 py-1" onClick={() => navigate('/confirm')}>Вернуться к протоколу</button>
        <button className="rounded border px-3 py-1" onClick={() => navigate('/')}>Открыть другой протокол</button>
      </div>
    </div>
  )
}
