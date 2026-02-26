import { useEffect, useState } from 'react'

export default function ToastNotification({ notification, onAction, onDismiss, index = 0 }) {
  const [isVisible, setIsVisible] = useState(true)
  const [isExiting, setIsExiting] = useState(false)

  useEffect(() => {
    // Auto-dismiss after 5 seconds
    const timer = setTimeout(() => {
      handleDismiss()
    }, 5000)

    return () => clearTimeout(timer)
  }, [])

  const handleDismiss = () => {
    setIsExiting(true)
    setTimeout(() => {
      setIsVisible(false)
      onDismiss?.()
    }, 300)
  }

  const handleAction = (action) => {
    onAction?.(action)
    handleDismiss()
  }

  if (!isVisible) return null

  return (
    <div
      className={`fixed right-6 w-96 bg-navy-800 border border-navy-600 rounded-xl shadow-2xl shadow-black/50 overflow-hidden transition-all duration-300 z-50 ${
        isExiting ? 'opacity-0 translate-x-full' : 'opacity-100 translate-x-0'
      }`}
      style={{ top: `${80 + index * 140}px` }}
    >
      {/* Progress bar */}
      <div className="h-1 bg-navy-700 relative overflow-hidden">
        <div className="absolute inset-0 bg-accent animate-progress-bar" />
      </div>

      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center">
              <svg className="w-4 h-4 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2a10 10 0 0 1 10 10c0 5.523-4.477 10-10 10a10 10 0 0 1-10-10A10 10 0 0 1 12 2z" />
                <circle cx="12" cy="12" r="3" />
                <path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
              </svg>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-100">{notification.title}</h4>
              <p className="text-xs text-slate-500">AI Assistant</p>
            </div>
          </div>
          <button
            onClick={handleDismiss}
            className="p-1 rounded hover:bg-navy-700 text-slate-400 hover:text-slate-200 transition-colors"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>

        {/* Message */}
        <p className="text-sm text-slate-300 mb-3 leading-relaxed">
          {notification.message}
        </p>

        {/* Actions */}
        {notification.actions && notification.actions.length > 0 && (
          <div className="flex flex-col gap-2">
            {notification.actions.map((action, index) => (
              <button
                key={index}
                onClick={() => handleAction(action)}
                className={`w-full px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  action.primary
                    ? 'bg-accent hover:bg-accent-dark text-navy-900'
                    : 'bg-navy-700 hover:bg-navy-600 text-slate-200'
                }`}
              >
                {action.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
