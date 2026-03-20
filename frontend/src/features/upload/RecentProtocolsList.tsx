import { Link } from 'react-router-dom'
import { Protocol } from '../../types/domain'

export function RecentProtocolsList({ protocols }: { protocols: Protocol[] }) {
  return (
    <div className="rounded border bg-white p-4">
      <h3 className="mb-3 text-sm font-semibold">Последние протоколы</h3>
      <div className="space-y-2">
        {protocols.map((p) => (
          <Link key={p.id} to={`/normalize?protocolId=${p.id}`} className="block rounded border p-2 text-sm hover:bg-slate-50">
            #{p.id} · {p.original_filename}
          </Link>
        ))}
      </div>
    </div>
  )
}
