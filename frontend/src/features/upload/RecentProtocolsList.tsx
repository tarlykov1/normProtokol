import { Link } from 'react-router-dom'
import { Protocol } from '../../types/domain'

interface Props {
  protocols: Protocol[]
  deletingId?: number | null
  onDelete: (protocol: Protocol) => void
}

export function RecentProtocolsList({ protocols, deletingId, onDelete }: Props) {
  return (
    <div className="rounded border bg-white p-4">
      <h3 className="mb-3 text-sm font-semibold">Последние протоколы</h3>
      <div className="space-y-2">
        {protocols.map((p) => (
          <div key={p.id} className="flex items-center gap-2 rounded border p-2 text-sm">
            <Link to={`/normalize?protocolId=${p.id}`} className="min-w-0 flex-1 truncate hover:underline" title={p.original_filename}>
              #{p.id} · {p.original_filename}
            </Link>
            <button
              className="rounded border border-red-300 px-2 py-1 text-xs text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
              onClick={() => onDelete(p)}
              disabled={deletingId === p.id}
            >
              {deletingId === p.id ? 'Удаляем…' : 'Удалить'}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
