import { useState, useEffect } from 'react'
import { getNotifications, updateNotification, markAllRead, deleteNotification } from '../../api/notifications'
import { formatTimestamp } from '../../utils/formatters'

export default function NotificationCenter({ isOpen, onClose, onAction }) {
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all') // 'all' or 'unread'

  useEffect(() => {
    if (isOpen) {
      loadNotifications()
    }
  }, [isOpen, filter])

  const loadNotifications = async () => {
    try {
      setLoading(true)
      const data = await getNotifications(filter === 'unread')
      setNotifications(data)
    } catch (error) {
      console.error('Failed to load notifications:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleMarkRead = async (id) => {
    try {
      await updateNotification(id, { is_read: true })
      setNotifications(prev =>
        prev.map(n => n.id === id ? { ...n, is_read: true } : n)
      )
    } catch (error) {
      console.error('Failed to mark as read:', error)
    }
  }

  const handleMarkAllRead = async () => {
    try {
      await markAllRead()
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
    } catch (error) {
      console.error('Failed to mark all as read:', error)
    }
  }

  const handleDelete = async (id) => {
    try {
      await deleteNotification(id)
      setNotifications(prev => prev.filter(n => n.id !== id))
    } catch (error) {
      console.error('Failed to delete notification:', error)
    }
  }

  const handleActionClick = async (notification, action) => {
    try {
      await updateNotification(notification.id, { 
        action_taken: action.id,
        is_read: true 
      })
      onAction?.(notification, action)
      onClose()
    } catch (error) {
      console.error('Failed to record action:', error)
    }
  }

  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed right-0 top-0 h-full w-[480px] bg-navy-800 border-l border-navy-600 z-50 flex flex-col shadow-2xl">
        {/* Header */}
        <div className="p-4 border-b border-navy-600">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-100">Notifications</h2>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-navy-700 text-slate-400 hover:text-slate-200 transition-colors"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>

          {/* Filter tabs */}
          <div className="flex gap-2">
            <button
              onClick={() => setFilter('all')}
              className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === 'all'
                  ? 'bg-accent text-navy-900'
                  : 'bg-navy-700 text-slate-300 hover:bg-navy-600'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter('unread')}
              className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === 'unread'
                  ? 'bg-accent text-navy-900'
                  : 'bg-navy-700 text-slate-300 hover:bg-navy-600'
              }`}
            >
              Unread
            </button>
            <button
              onClick={handleMarkAllRead}
              className="px-3 py-2 rounded-lg text-sm font-medium bg-navy-700 text-slate-300 hover:bg-navy-600 transition-colors"
            >
              Mark all read
            </button>
          </div>
        </div>

        {/* Notifications list */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
            </div>
          ) : notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-32 text-slate-500">
              <svg className="w-12 h-12 mb-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <p className="text-sm">No notifications</p>
            </div>
          ) : (
            <div className="p-2 space-y-2">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 rounded-lg border transition-colors ${
                    notification.is_read
                      ? 'bg-navy-900/50 border-navy-700'
                      : 'bg-navy-700 border-accent/30'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {!notification.is_read && (
                          <div className="w-2 h-2 rounded-full bg-accent" />
                        )}
                        <h4 className="text-sm font-semibold text-slate-100">
                          {notification.title}
                        </h4>
                      </div>
                      <p className="text-xs text-slate-500">
                        {formatTimestamp(notification.created_at)}
                      </p>
                    </div>
                    <div className="flex gap-1">
                      {!notification.is_read && (
                        <button
                          onClick={() => handleMarkRead(notification.id)}
                          className="p-1 rounded hover:bg-navy-600 text-slate-400 hover:text-slate-200"
                          title="Mark as read"
                        >
                          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M5 13l4 4L19 7" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(notification.id)}
                        className="p-1 rounded hover:bg-red-500/20 text-slate-400 hover:text-red-400"
                        title="Delete"
                      >
                        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M6 18L18 6M6 6l12 12" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      </button>
                    </div>
                  </div>

                  <p className="text-sm text-slate-300 mb-3 leading-relaxed">
                    {notification.message}
                  </p>

                  {notification.actions && notification.actions.length > 0 && (
                    <div className="flex gap-2">
                      {notification.actions.map((action, index) => (
                        <button
                          key={index}
                          onClick={() => handleActionClick(notification, action)}
                          className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                            action.primary
                              ? 'bg-accent hover:bg-accent-dark text-navy-900'
                              : 'bg-navy-600 hover:bg-navy-500 text-slate-200'
                          }`}
                        >
                          {action.label}
                        </button>
                      ))}
                    </div>
                  )}

                  {notification.action_taken && (
                    <div className="mt-2 text-xs text-slate-500">
                      Action taken: {notification.action_taken}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  )
}
