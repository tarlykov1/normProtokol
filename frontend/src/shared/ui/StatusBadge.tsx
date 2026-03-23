import { cn } from '../lib/cn'

export function StatusBadge({ status }: { status: 'ok' | 'warning' | 'error' | 'draft' }) {
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
  return <span className={cn('rounded px-2 py-1 text-xs font-medium', c)}>{label}</span>
}
