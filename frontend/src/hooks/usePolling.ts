import { useEffect, useRef, useCallback } from 'react'

export function usePolling(fn: () => Promise<void> | void, intervalMs: number, enabled = true) {
  const fnRef = useRef(fn)
  const mountedRef = useRef(true)

  fnRef.current = fn

  const safeFn = useCallback(async () => {
    if (!mountedRef.current) return
    try {
      await fnRef.current()
    } catch {
      // Silently handle errors — don't crash the component
    }
  }, [])

  useEffect(() => {
    mountedRef.current = true
    if (!enabled) return

    // Small delay on first call to let component mount fully
    const initTimeout = setTimeout(safeFn, 100)
    const id = setInterval(safeFn, intervalMs)

    return () => {
      mountedRef.current = false
      clearTimeout(initTimeout)
      clearInterval(id)
    }
  }, [intervalMs, enabled, safeFn])
}
