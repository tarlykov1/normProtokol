import { useEffect } from 'react'

export type ToastKind = 'success' | 'error'

export interface ToastMessage {
  id: number
  kind: ToastKind
  text: string
  detail?: string
}

interface Props {
  toasts: ToastMessage[]
  onClose: (id: number) => void
}

const AUTO_CLOSE_MS = 5000

export function ToastStack({ toasts, onClose }: Props) {
  useEffect(() => {
    if (!toasts.length) return
    const timers = toasts.map((toast) =>
      window.setTimeout(() => onClose(toast.id), AUTO_CLOSE_MS)
    )
    return () => timers.forEach((timer) => window.clearTimeout(timer))
  }, [toasts, onClose])

  return (
    <div className="fixed bottom-4 right-4 z-50 flex w-[min(92vw,420px)] flex-col gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={toast.kind === 'success'
            ? 'rounded border border-emerald-300 bg-emerald-50 p-3 text-emerald-900 shadow'
            : 'rounded border border-red-300 bg-red-50 p-3 text-red-900 shadow-md'}
          role="status"
          aria-live="polite"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-medium">{toast.text}</p>
              {toast.detail && <p className="mt-1 text-xs opacity-90">{toast.detail}</p>}
            </div>
            <button className="rounded border px-1.5 py-0.5 text-xs" onClick={() => onClose(toast.id)}>
              ×
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
