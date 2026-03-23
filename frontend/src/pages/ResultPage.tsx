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
      <p className="text-sm">ID смарт-процесса: {result.smart_process_id ?? 'не создан'}</p>
      <p className="text-sm">Опубликовано: {result.published_tasks.length}, пропущено: {result.skipped_tasks.length}</p>
      <p className="text-xs text-slate-600">Пропущенные задачи не потеряны: их можно доработать на этапе нормализации.</p>

      {result.skipped_details.length > 0 && (
        <div className="rounded border border-amber-200 bg-amber-50 p-3 text-sm">
          <p className="mb-2 font-medium">Пропущенные задачи</p>
          <ul className="space-y-2">
            {result.skipped_details.map((item) => (
              <li key={item.task_id} className="rounded border border-amber-200 bg-white p-2">
                <p className="font-medium">#{item.task_id}: {item.normalized_text || 'Без текста задачи'}</p>
                <p>Причина: {item.reason}</p>
                <p>Исполнитель: {item.assignee_b24_name ?? item.assignee_raw ?? 'не указан'}</p>
                {(item.errors.length > 0 || item.warnings.length > 0) && (
                  <p className="text-xs text-slate-700">{[...item.errors, ...item.warnings].join('; ')}</p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {result.errors.length > 0 && <pre className="rounded bg-red-50 p-2 text-xs text-red-700">{JSON.stringify(result.errors, null, 2)}</pre>}
      <div className="flex gap-2">
        <button className="rounded bg-amber-600 px-3 py-1 text-white" onClick={() => navigate('/normalize')}>Вернуться к протоколу и исправить</button>
        <button className="rounded border px-3 py-1" onClick={() => navigate('/confirm')}>К подтверждению</button>
        <button className="rounded border px-3 py-1" onClick={() => navigate('/')}>Открыть другой протокол</button>
      </div>
    </div>
  )
}
