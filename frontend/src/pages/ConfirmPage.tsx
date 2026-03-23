import { useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { protocolsApi } from '../shared/api/protocolsApi'
import { downloadBlob } from '../shared/lib/file'
import { useProtocol } from '../features/protocol/useProtocolQueries'
import { ValidationSummary } from '../types/domain'

export function ConfirmPage() {
  const [params] = useSearchParams()
  const protocolId = Number(params.get('protocolId') || localStorage.getItem('lastProtocolId'))
  const { data, refetch } = useProtocol(protocolId)
  const [summary, setSummary] = useState<ValidationSummary | null>(null)
  const navigate = useNavigate()

  const assigneeIssues = useMemo(() => {
    if (!summary) return []
    return summary.details.filter((item) => {
      const combined = [...item.errors, ...item.warnings].join(' ').toLowerCase()
      return combined.includes('исполнител') || combined.includes('bitrix24')
    })
  }, [summary])

  if (!data) return null

  return (
    <div className="space-y-3 rounded border bg-white p-4">
      <h2 className="text-lg font-semibold">Подтверждение</h2>
      <p className="text-sm">Тем: {data.topics.length}, задач: {data.tasks.length}, ошибок: {data.tasks.filter((t) => t.errors.length).length}</p>
      {summary && <p className="text-sm">Валидно: {summary.count_valid}, предупреждений: {summary.count_warnings}, ошибок: {summary.count_errors}</p>}

      {assigneeIssues.length > 0 && (
        <div className="rounded border border-amber-200 bg-amber-50 p-3 text-sm">
          <p className="mb-1 font-medium">Проблемы с исполнителями</p>
          <ul className="list-disc space-y-1 pl-5">
            {assigneeIssues.map((item) => (
              <li key={item.task_id}>Задача #{item.task_id}: {[...item.errors, ...item.warnings].join('; ')}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <button className="rounded border px-3 py-1" onClick={() => protocolsApi.saveDraft(data.id)}>Сохранить черновик</button>
        <button className="rounded border px-3 py-1" onClick={async () => setSummary(await protocolsApi.validate(data.id))}>Валидировать</button>
        <button className="rounded border px-3 py-1" onClick={async () => { await protocolsApi.generateDocx(data.id); await refetch() }}>Сформировать DOCX</button>
        <button className="rounded border px-3 py-1" onClick={async () => downloadBlob(await protocolsApi.downloadDocx(data.id), `protocol-${data.id}.docx`)}>Скачать DOCX</button>
        <button className="rounded bg-green-700 px-3 py-1 text-white" onClick={async () => { const res = await protocolsApi.publish(data.id); navigate('/result', { state: res }) }}>Отправить в Bitrix24</button>
      </div>
    </div>
  )
}
