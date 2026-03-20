import { useEffect, useRef } from 'react'

export function useAutosaveDraft(enabled: boolean, onSave: () => Promise<void>, delay = 1400) {
  const tRef = useRef<number | null>(null)

  useEffect(() => {
    if (!enabled) return
    if (tRef.current) window.clearTimeout(tRef.current)
    tRef.current = window.setTimeout(() => { void onSave() }, delay)
    return () => { if (tRef.current) window.clearTimeout(tRef.current) }
  }, [enabled, onSave, delay])
}
