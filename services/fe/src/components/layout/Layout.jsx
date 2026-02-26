import { useState, useEffect } from 'react'
import Header from './Header'
import Nav from './Nav'
import { useChat } from '../../hooks/useChat'
import ChatContainer from '../assistant/ChatContainer'
import ToastNotification from '../common/ToastNotification'
import NotificationCenter from '../common/NotificationCenter'
import { listConversations, createConversation, updateConversation, deleteConversation } from '../../api/conversations'

export default function Layout({ children }) {
  const [isAssistantOpen, setIsAssistantOpen] = useState(false)
  const [isNotificationCenterOpen, setIsNotificationCenterOpen] = useState(false)
  const [toastNotifications, setToastNotifications] = useState([])
  const [isHistoryOpen, setIsHistoryOpen] = useState(false)
  const [conversations, setConversations] = useState([])
  const [currentConversationId, setCurrentConversationId] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [editingTitle, setEditingTitle] = useState('')
  const { messages, sendMessage, isLoading, toolActivity, connected, error, conversationId } = useChat('Assistant', currentConversationId)

  // Sync initial conversation ID from useChat so currentConversationId is never stale
  useEffect(() => {
    if (conversationId && !currentConversationId) {
      setCurrentConversationId(conversationId)
    }
  }, [conversationId])

  // Load conversations on mount
  useEffect(() => {
    if (isAssistantOpen) {
      loadConversations()
    }
  }, [isAssistantOpen])

  const loadConversations = async () => {
    try {
      const data = await listConversations()
      setConversations(data || [])
    } catch (error) {
      console.error('Failed to load conversations:', error)
    }
  }

  const handleNewChat = async () => {
    try {
      const newConv = await createConversation('New Chat')
      setCurrentConversationId(newConv.id)
      setIsHistoryOpen(false)
      await loadConversations()
    } catch (error) {
      console.error('Failed to create conversation:', error)
    }
  }

  const handleSelectConversation = (convId) => {
    setCurrentConversationId(convId)
    setIsHistoryOpen(false)
  }

  const handleRenameStart = (conv) => {
    setEditingId(conv.id)
    setEditingTitle(conv.title || 'Untitled Chat')
  }

  const handleRenameSubmit = async (convId) => {
    if (!editingTitle.trim()) return
    
    try {
      await updateConversation(convId, editingTitle)
      await loadConversations()
      setEditingId(null)
      setEditingTitle('')
    } catch (error) {
      console.error('Failed to rename conversation:', error)
    }
  }

  const handleRenameCancel = () => {
    setEditingId(null)
    setEditingTitle('')
  }

  const handleDelete = async (convId) => {
    if (!confirm('Are you sure you want to delete this conversation?')) return
    
    try {
      await deleteConversation(convId)
      await loadConversations()
      if (currentConversationId === convId) {
        setCurrentConversationId(null)
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error)
    }
  }

  const handleNotificationAction = async (notification, action) => {
    if (action.type === 'open_chat') {
      setIsAssistantOpen(true)
      try {
        const newConv = await createConversation('New Chat')
        setCurrentConversationId(newConv.id)
      } catch (error) {
        console.error('Failed to create conversation:', error)
      }
      if (action.message) {
        setTimeout(() => sendMessage(action.message), 500)
      }
    } else if (action.type === 'execute') {
      // Execute action directly
      console.log('Executing action:', action)
      // Add your action execution logic here
    }
  }

  const removeToastNotification = (id) => {
    setToastNotifications(prev => prev.filter(n => n.id !== id))
  }

  return (
    <div className="h-screen bg-navy-900 flex flex-col overflow-hidden">
      <Header 
        onToggleAssistant={() => setIsAssistantOpen(!isAssistantOpen)} 
        isAssistantOpen={isAssistantOpen}
        onNotificationClick={() => setIsNotificationCenterOpen(true)}
      />
      <div className="flex flex-1 overflow-hidden">
        <Nav onNotificationClick={() => setIsNotificationCenterOpen(true)} />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
        
        {/* AI Assistant Side Panel */}
        <div
          className={`w-[480px] bg-navy-800 border-l border-navy-600 flex flex-col overflow-hidden transition-all duration-300 relative ${
            isAssistantOpen ? 'flex' : 'hidden'
          }`}
        >
          {/* Panel Header */}
          <div className="flex items-center justify-between p-4 border-b border-navy-600">
            <div className="flex items-center gap-3">
              {/* Hamburger Menu */}
              <button
                onClick={() => setIsHistoryOpen(!isHistoryOpen)}
                className="p-1.5 rounded-lg hover:bg-navy-700 text-slate-400 hover:text-slate-200 transition-colors"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M3 12h18M3 6h18M3 18h18" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
              
              <svg className="w-6 h-6 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2a10 10 0 0 1 10 10c0 5.523-4.477 10-10 10a10 10 0 0 1-10-10A10 10 0 0 1 12 2z" />
                <circle cx="12" cy="12" r="3" />
                <path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
              </svg>
              <div>
                <h2 className="text-lg font-semibold text-slate-100">AI Assistant</h2>
                <p className="text-xs text-slate-500">Natural language trading interface</p>
              </div>
            </div>
            <button
              onClick={() => setIsAssistantOpen(false)}
              className="p-1.5 rounded-lg hover:bg-navy-700 text-slate-400 hover:text-slate-200 transition-colors"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>

          {/* Chat History Sidebar */}
          {isHistoryOpen && (
            <div className="absolute left-0 top-0 w-64 h-full bg-navy-900 border-r border-navy-600 z-50 flex flex-col">
              {/* History Header */}
              <div className="p-4 border-b border-navy-600">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-slate-100">Chat History</h3>
                  <button
                    onClick={() => setIsHistoryOpen(false)}
                    className="p-1 rounded hover:bg-navy-700 text-slate-400 hover:text-slate-200"
                  >
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </button>
                </div>
                <button
                  onClick={handleNewChat}
                  className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-accent hover:bg-accent-dark text-navy-900 rounded-lg font-medium text-sm transition-colors"
                >
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 5v14M5 12h14" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  New Chat
                </button>
              </div>

              {/* Conversations List */}
              <div className="flex-1 overflow-y-auto p-2">
                {conversations.length === 0 ? (
                  <div className="text-center text-slate-500 text-sm py-8">
                    No conversations yet
                  </div>
                ) : (
                  conversations.map((conv) => (
                    <div
                      key={conv.id}
                      className={`group relative rounded-lg mb-1 transition-colors ${
                        currentConversationId === conv.id
                          ? 'bg-navy-700'
                          : 'hover:bg-navy-800'
                      }`}
                    >
                      {editingId === conv.id ? (
                        <div className="p-3">
                          <input
                            type="text"
                            value={editingTitle}
                            onChange={(e) => setEditingTitle(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleRenameSubmit(conv.id)
                              if (e.key === 'Escape') handleRenameCancel()
                            }}
                            className="w-full px-2 py-1 text-sm bg-navy-600 text-slate-100 rounded border border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                            autoFocus
                          />
                          <div className="flex gap-1 mt-2">
                            <button
                              onClick={() => handleRenameSubmit(conv.id)}
                              className="flex-1 px-2 py-1 text-xs bg-accent text-navy-900 rounded hover:bg-accent-dark"
                            >
                              Save
                            </button>
                            <button
                              onClick={handleRenameCancel}
                              className="flex-1 px-2 py-1 text-xs bg-navy-600 text-slate-300 rounded hover:bg-navy-500"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <>
                          <button
                            onClick={() => handleSelectConversation(conv.id)}
                            className="w-full text-left p-3"
                          >
                            <div className={`text-sm font-medium truncate ${
                              currentConversationId === conv.id ? 'text-slate-100' : 'text-slate-400'
                            }`}>
                              {conv.title || 'Untitled Chat'}
                            </div>
                            <div className="text-xs text-slate-500 mt-1">
                              {new Date(conv.created_at).toLocaleDateString()}
                            </div>
                          </button>
                          <div className="absolute right-2 top-2 hidden group-hover:flex gap-1">
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleRenameStart(conv)
                              }}
                              className="p-1 rounded hover:bg-navy-600 text-slate-400 hover:text-slate-200"
                              title="Rename"
                            >
                              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                              </svg>
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleDelete(conv.id)
                              }}
                              className="p-1 rounded hover:bg-red-500/20 text-slate-400 hover:text-red-400"
                              title="Delete"
                            >
                              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                              </svg>
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
          
          {/* Chat Container */}
          <div className="flex-1 overflow-hidden">
            <ChatContainer
              messages={messages}
              onSend={sendMessage}
              isLoading={isLoading}
              toolActivity={toolActivity}
            />
          </div>
        </div>
      </div>

      {/* Toast Notifications */}
      {toastNotifications.map((notification, index) => (
        <ToastNotification
          key={notification.id}
          index={index}
          notification={notification}
          onAction={(action) => {
            handleNotificationAction(notification, action)
            removeToastNotification(notification.id)
          }}
          onDismiss={() => removeToastNotification(notification.id)}
        />
      ))}

      {/* Notification Center */}
      <NotificationCenter
        isOpen={isNotificationCenterOpen}
        onClose={() => setIsNotificationCenterOpen(false)}
        onAction={handleNotificationAction}
      />
    </div>
  )
}
