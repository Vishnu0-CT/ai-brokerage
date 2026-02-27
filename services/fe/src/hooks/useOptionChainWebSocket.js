import { useState, useEffect, useRef } from 'react'
import { BE_BASE_URL } from '../config'

/**
 * Custom hook for real-time option chain updates via WebSocket
 */
export function useOptionChainWebSocket(symbol, expiry, enabled = true) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [connected, setConnected] = useState(false)
  
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const reconnectAttemptsRef = useRef(0)
  const instanceIdRef = useRef(Math.random().toString(36).substr(2, 9))

  useEffect(() => {
    // 1. Guard: Check if we should even attempt a connection
    if (!enabled || !symbol || !expiry) {
      setLoading(false)
      setConnected(false)
      return
    }

    // 2. Local flag to prevent race conditions during async setup
    let isCurrentEffect = true

    const connect = () => {
      // Don't start if the effect has already been cleaned up
      if (!isCurrentEffect) return

      // Determine WebSocket URL
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      let wsHost = BE_BASE_URL ? BE_BASE_URL.replace(/^https?:\/\//, '') : 'localhost:8000'
      const wsUrl = `${wsProtocol}//${wsHost}/api/option-chain/stream`

      console.log(`[HOOK ${instanceIdRef.current}] Connecting: ${wsUrl}`)
      
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        // If the component unmounted/changed while connecting, kill this socket
        if (!isCurrentEffect) {
          ws.close()
          return
        }

        console.log(`[HOOK ${instanceIdRef.current}] Connected to ${symbol}`)
        setConnected(true)
        setError(null)
        setLoading(false)
        reconnectAttemptsRef.current = 0
        
        ws.send(JSON.stringify({ symbol, expiry }))
      }

      ws.onmessage = (event) => {
        if (!isCurrentEffect) return
        try {
          const message = JSON.parse(event.data)
          if (message.type === 'option_chain') {
            setData(message.data)
            setLoading(false)
          } else if (message.type === 'error') {
            setError(message.message)
          }
        } catch (err) {
          console.error('WS Parse Error:', err)
        }
      }

      ws.onerror = (event) => {
        if (!isCurrentEffect) return
        console.error(`[HOOK ${instanceIdRef.current}] WS Error`)
        setError('WebSocket connection error')
      }

      ws.onclose = (e) => {
        // Only reconnect if this effect is still the "active" one
        if (isCurrentEffect) {
          setConnected(false)
          console.log(`[HOOK ${instanceIdRef.current}] Disconnected. Reconnecting...`)
          
          if (reconnectAttemptsRef.current < 5) {
            const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000)
            reconnectTimeoutRef.current = setTimeout(() => {
              reconnectAttemptsRef.current++
              connect()
            }, delay)
          }
        }
      }
    }

    connect()

    // 3. Cleanup Function
    return () => {
      console.log(`[HOOK ${instanceIdRef.current}] Cleaning up ${symbol}`)
      isCurrentEffect = false // This stops any pending async logic/reconnects
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }

      if (wsRef.current) {
        // Remove listeners so they don't fire during the closing process
        wsRef.current.onopen = null
        wsRef.current.onmessage = null
        wsRef.current.onerror = null
        wsRef.current.onclose = null
        
        if (wsRef.current.readyState !== WebSocket.CLOSED) {
          wsRef.current.close()
        }
        wsRef.current = null
      }
    }
  }, [symbol, expiry, enabled]) // React will re-run this only when these change

  return { data, loading, error, connected }
}