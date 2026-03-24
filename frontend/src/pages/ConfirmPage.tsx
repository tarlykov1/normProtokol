import { useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { protocolsApi } from '../shared/api/protocolsApi'
import { downloadBlob } from '../shared/lib/file'
import { useProtocol } from '../features/protocol/useProtocolQueries'
import { ValidationSummary } from '../types/domain'

const normalizeMessage = (msg: string) => {
  const lowered = msg.toLowerCase()
  if (lowered.includes('несколько исполнителей')) return 'Указано несколько исполнителей (это допустимо).'
  if (lowered.includes('text_deadline') || lowered.includes('deadline_kind')) return 'Срок указан текстом. При необходимости уточните дату.'
  return msg
}

export function ConfirmPage() {
  const [params] = useSearchParams()
  const protocolId = Number(params.get('protocolId') || localStorage.getItem('lastProtocolId'))
  const { data, refetch } = useProtocol(protocolId)
  const [summary, setSummary] = useState<ValidationSummary | null>(null)
  const navigate = useNavigate()

  const tasks = useMemo(() => (data?.tasks ?? []).filter((t) => t.item_kind === 'task'), [data])

  const grouped = useMemo(() => {
    return {
      ready: tasks.filter((task) => task.status === 'valid').length,
      review: tasks.filter((task) => task.status === 'needs_review').length,
      completion: tasks.filter((task) => task.status === 'needs_completion').length,
      excluded: tasks.filter((task) => task.status === 'excluded').length
    }
  }, [tasks])

  if (!data) return null

  return (
    <div className="space-y-3 rounded border bg-white p-4">
      <h2 className="text-lg font-semibold">Подтверждение</h2>
      <p className="text-sm">Тип документа: {data.protocol_type}</p>
      <p className="text-sm">Готовы: {grouped.ready}, требуют проверки: {grouped.review}, требуют доработки: {grouped.completion}, исключены: {grouped.excluded}</p>
      {summary && <p className="text-sm">Валидно: {summary.count_valid}, предупреждений: {summary.count_warnings}, ошибок: {summary.count_errors}</p>}

      <div className="flex flex-wrap gap-2">
        <button className="rounded border px-3 py-1" onClick={() => protocolsApi.saveDraft(data.id)}>Сохранить черновик</button>
        <button className="rounded border px-3 py-1" onClick={async () => setSummary(await protocolsApi.validate(data.id))}>Валидировать</button>
        <button className="rounded border px-3 py-1" onClick={async () => { await protocolsApi.generateDocx(data.id); await refetch() }}>Сформировать DOCX</button>
        <button className="rounded border px-3 py-1" onClick={async () => downloadBlob(await protocolsApi.downloadDocx(data.id), `protocol-${data.id}.docx`)}>Скачать DOCX</button>
        <button className="rounded bg-green-700 px-3 py-1 text-white" onClick={async () => { const res = await protocolsApi.publish(data.id); navigate('/result', { state: res }) }}>Отправить в Bitrix24</button>
      </div>

      <div className="space-y-2">
        {tasks.map((task) => (
          <div key={task.id} className="rounded border p-2 text-sm">
            <p className="font-medium">#{task.id} {task.normalized_text}</p>
            <p className="text-xs text-slate-600">Исполнители: {task.assignees_display || task.assignee_b24_name || task.assignee_raw || '—'}</p>
            <p className="text-xs text-slate-600">Срок: {task.deadline_iso || task.deadline_raw || task.deadline_note || '—'}</p>
            {task.coordinator && <p className="text-xs text-slate-600">Координатор: {task.coordinator}</p>}
            {(task.errors.length > 0 || task.warnings.length > 0) && (
              <div className="mt-1 grid gap-1 text-xs">
                {task.errors.map((m, idx) => <p key={`e-${idx}`} className="text-red-700">Ошибка: {normalizeMessage(m)}</p>)}
                {task.warnings.map((m, idx) => <p key={`w-${idx}`} className="text-amber-700">Предупреждение: {normalizeMessage(m)}</p>)}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
