import { useState, useEffect, useRef, useCallback } from 'react'
import { AI_WS_URL } from '../config'

const MIN_RECONNECT_DELAY = 1000
const MAX_RECONNECT_DELAY = 30000

/**
 * WebSocket connection manager.
 * Connects to ws://host/ws/chat/{conversationId} via Vite proxy.
 * Auto-reconnects with exponential backoff.
 */
export function useWebSocket(conversationId, { onMessage } = {}) {
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)
  const reconnectDelay = useRef(MIN_RECONNECT_DELAY)
  const reconnectTimer = useRef(null)
  const onMessageRef = useRef(onMessage)
  const mountedRef = useRef(true)

  // Keep callback ref up-to-date without triggering reconnect
  useEffect(() => { onMessageRef.current = onMessage }, [onMessage])

  const connect = useCallback(() => {
    if (!conversationId || !mountedRef.current) return

    // Use relative path so Vite proxy handles it in dev
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = AI_WS_URL.startsWith('ws')
      ? `${AI_WS_URL}/ws/chat/${conversationId}`
      : `${protocol}//${window.location.host}/ws/chat/${conversationId}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      if (!mountedRef.current) return
      setConnected(true)
      reconnectDelay.current = MIN_RECONNECT_DELAY
    }

    ws.onmessage = (event) => {
      if (!mountedRef.current) return
      try {
        const msg = JSON.parse(event.data)
        onMessageRef.current?.(msg)
      } catch {
        // ignore non-JSON messages
      }
    }

    ws.onclose = () => {
      if (!mountedRef.current) return
      setConnected(false)
      // Schedule reconnect with exponential backoff
      reconnectTimer.current = setTimeout(() => {
        reconnectDelay.current = Math.min(
          reconnectDelay.current * 2,
          MAX_RECONNECT_DELAY,
        )
        connect()
      }, reconnectDelay.current)
    }

    ws.onerror = () => {
      // onclose will fire after onerror — reconnect is handled there
    }
  }, [conversationId])

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimer.current)
    if (wsRef.current) {
      wsRef.current.onclose = null // prevent reconnect loop
      wsRef.current.close()
      wsRef.current = null
    }
    setConnected(false)
  }, [])

  const send = useCallback((content) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'text', content }))
    }
  }, [])

  useEffect(() => {
    mountedRef.current = true
    connect()
    return () => {
      mountedRef.current = false
      disconnect()
    }
  }, [connect, disconnect])

  return { send, connected, disconnect }
}
