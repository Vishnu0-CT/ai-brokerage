import { useState, useRef, useEffect } from 'react'

export default function ChatInput({ onSend, isLoading, disabled }) {
  const [message, setMessage] = useState('')
  const inputRef = useRef(null)

  useEffect(() => {
    if (!isLoading && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isLoading])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (message.trim() && !isLoading && !disabled) {
      onSend(message)
      setMessage('')
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className="flex items-end gap-3 p-4 bg-navy-800 border border-navy-600 rounded-2xl focus-within:border-accent/50 transition-colors">
        <textarea
          ref={inputRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your portfolio, risk, or trades..."
          disabled={isLoading || disabled}
          rows={1}
          className="flex-1 bg-transparent text-slate-200 placeholder-slate-500 resize-none outline-none text-sm leading-relaxed max-h-32"
          style={{ minHeight: '24px' }}
        />

        <button
          type="submit"
          disabled={!message.trim() || isLoading || disabled}
          className={`flex items-center justify-center w-10 h-10 rounded-xl transition-all ${
            message.trim() && !isLoading
              ? 'bg-accent text-navy-900 hover:bg-accent-light'
              : 'bg-navy-700 text-slate-500 cursor-not-allowed'
          }`}
        >
          {isLoading ? (
            <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeDasharray="32" strokeLinecap="round" />
            </svg>
          ) : (
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          )}
        </button>
      </div>

      {/* Character hint */}
      <div className="absolute -bottom-6 left-4 text-xs text-slate-600">
        Press Enter to send, Shift+Enter for new line
      </div>
    </form>
  )
}
