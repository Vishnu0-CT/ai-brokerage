import { useState, useEffect, useCallback, useRef } from 'react'

/**
 * Generic data fetcher hook.
 * Wraps any async API call with { data, loading, error, refetch }.
 * Cancels in-flight requests on unmount.
 *
 * @param {Function} apiFn - async function returning data
 * @param {Array} deps - dependency array (re-fetches when deps change)
 * @param {object} options - { skip: boolean } to conditionally skip fetching
 */
export function useApi(apiFn, deps = [], options = {}) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(!options.skip)
  const [error, setError] = useState(null)
  const abortRef = useRef(null)
  const mountedRef = useRef(true)

  const fetch = useCallback(async () => {
    if (options.skip) return

    // Abort any in-flight request
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setLoading(true)
    setError(null)

    try {
      const result = await apiFn({ signal: controller.signal })
      if (mountedRef.current && !controller.signal.aborted) {
        setData(result)
      }
    } catch (err) {
      if (err.name === 'AbortError') return
      if (mountedRef.current) {
        setError(err)
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false)
      }
    }
  }, deps) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    mountedRef.current = true
    fetch()
    return () => {
      mountedRef.current = false
      abortRef.current?.abort()
    }
  }, [fetch])

  return { data, loading, error, refetch: fetch }
}
