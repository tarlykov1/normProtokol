import { cn } from '../lib/cn'

interface Props {
  status: 'ok' | 'warning' | 'error' | 'draft'
  messages?: string[]
}

export function StatusBadge({ status, messages = [] }: Props) {
  const c = {
    ok: 'bg-green-100 text-green-700',
    warning: 'bg-amber-100 text-amber-700',
    error: 'bg-red-100 text-red-700',
    draft: 'bg-slate-200 text-slate-600'
  }[status]
  const label = {
    ok: 'ОК',
    warning: 'Предупреждение',
    error: 'Ошибка',
    draft: 'Черновик'
  }[status]
  return (
    <div className="space-y-1">
      <span className={cn('inline-flex rounded px-2 py-1 text-xs font-medium', c)}>{label}</span>
      {messages.length > 0 && (
        <ul className="space-y-0.5 text-xs text-slate-700">
          {messages.map((message, index) => (
            <li key={`${status}-${index}`} className="leading-4">
              • {message}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
