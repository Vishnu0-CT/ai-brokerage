import { useState, useCallback, useRef, useEffect } from 'react'
import { createConversation, getConversation, saveMessage } from '../api/conversations'
import { useWebSocket } from './useWebSocket'

/**
 * Complete chat hook that orchestrates:
 * 1. Create/load conversation via BE REST
 * 2. Connect WebSocket to AI service
 * 3. Optimistic user message rendering
 * 4. Handle { type: "response" } and { type: "tool_activity" } from WS
 * 5. Save messages to BE for persistence
 */
export function useChat(conversationTitle = 'Chat') {
  const [conversationId, setConversationId] = useState(null)
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [toolActivity, setToolActivity] = useState(null)
  const [error, setError] = useState(null)
  const pendingRef = useRef(false)

  // Initialize conversation
  useEffect(() => {
    let cancelled = false

    async function init() {
      try {
        const conv = await createConversation(conversationTitle)
        if (!cancelled) {
          setConversationId(conv.id)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Failed to create conversation')
        }
      }
    }

    init()
    return () => { cancelled = true }
  }, [conversationTitle])

  const streamingMessageRef = useRef(null)

  // Handle incoming WS messages
  const handleWsMessage = useCallback((msg) => {
    if (msg.type === 'tool_activity') {
      setToolActivity(msg)
    } else if (msg.type === 'response_chunk') {
      // Streaming chunk received - update message in real-time
      setMessages(prev => {
        const lastMsg = prev[prev.length - 1]
        
        if (lastMsg && lastMsg.role === 'assistant' && lastMsg.isStreaming) {
          // Update existing streaming message
          return [
            ...prev.slice(0, -1),
            {
              ...lastMsg,
              content: lastMsg.content + msg.content,
            }
          ]
        } else {
          // Create new streaming message
          const newMsg = {
            id: `msg_${Date.now()}`,
            role: 'assistant',
            content: msg.content,
            isStreaming: true,
            timestamp: new Date().toISOString(),
          }
          streamingMessageRef.current = newMsg.id
          return [...prev, newMsg]
        }
      })
    } else if (msg.type === 'response_complete') {
      // Streaming complete - finalize message
      setToolActivity(null)
      pendingRef.current = false
      setIsLoading(false)

      setMessages(prev => {
        const lastMsg = prev[prev.length - 1]
        if (lastMsg && lastMsg.role === 'assistant' && lastMsg.isStreaming) {
          const finalMsg = {
            ...lastMsg,
            isStreaming: false,
            content: msg.detail || lastMsg.content,
          }
          
          // Persist final message to BE
          if (conversationId) {
            saveMessage(conversationId, {
              role: 'assistant',
              content: finalMsg.content,
            }).catch(() => {})
          }
          
          return [...prev.slice(0, -1), finalMsg]
        }
        return prev
      })

      streamingMessageRef.current = null
    } else if (msg.type === 'response') {
      // Fallback for non-streaming responses
      setToolActivity(null)
      pendingRef.current = false
      setIsLoading(false)

      const assistantMessage = {
        id: `msg_${Date.now()}`,
        role: 'assistant',
        content: msg.detail || msg.voice || '',
        voice: msg.voice || '',
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, assistantMessage])

      // Persist assistant message to BE
      if (conversationId) {
        saveMessage(conversationId, {
          role: 'assistant',
          content: assistantMessage.content,
        }).catch(() => {})
      }
    }
  }, [conversationId])

  const { send: wsSend, connected } = useWebSocket(conversationId, {
    onMessage: handleWsMessage,
  })

  const sendMessage = useCallback(async (content) => {
    if (!content.trim() || pendingRef.current) return

    const userMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }

    // Optimistic render
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setError(null)
    pendingRef.current = true

    // Persist user message to BE
    if (conversationId) {
      saveMessage(conversationId, {
        role: 'user',
        content,
      }).catch(() => {})
    }

    // Send via WebSocket
    wsSend(content)
  }, [conversationId, wsSend])

  const clearMessages = useCallback(() => {
    setMessages([])
    setError(null)
    setToolActivity(null)
  }, [])

  // Load existing messages if conversation has history
  useEffect(() => {
    if (!conversationId) return
    let cancelled = false

    async function loadHistory() {
      try {
        const conv = await getConversation(conversationId)
        if (!cancelled && conv.messages?.length > 0) {
          setMessages(conv.messages.map(m => ({
            id: m.id,
            role: m.role,
            content: m.content,
            timestamp: m.created_at,
          })))
        }
      } catch {
        // Conversation may be new, no history to load
      }
    }

    loadHistory()
    return () => { cancelled = true }
  }, [conversationId])

  return {
    messages,
    sendMessage,
    isLoading,
    toolActivity,
    connected,
    error,
    clearMessages,
    conversationId,
  }
}
