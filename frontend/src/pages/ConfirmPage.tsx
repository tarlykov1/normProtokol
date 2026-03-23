import { useState } from 'react'
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
  if (!data) return null

  return (
    <div className="space-y-3 rounded border bg-white p-4">
      <h2 className="text-lg font-semibold">Подтверждение</h2>
      <p className="text-sm">Тем: {data.topics.length}, задач: {data.tasks.length}, ошибок: {data.tasks.filter((t) => t.errors.length).length}</p>
      {summary && <p className="text-sm">Валидно: {summary.count_valid}, предупреждений: {summary.count_warnings}, ошибок: {summary.count_errors}</p>}
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
