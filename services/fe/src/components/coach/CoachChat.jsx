import { useState, useRef, useEffect } from 'react'
import { useChat } from '../../hooks/useChat'
import { formatTimestamp } from '../../utils/formatters'

const SUGGESTED_QUESTIONS = [
  'What are my biggest trading mistakes this month?',
  'When is my best time to trade?',
  'How can I improve my win rate?',
  'Am I holding losers too long?',
  'What instruments should I focus on?',
  'How is my risk management?',
]

export default function CoachChat() {
  const { messages, sendMessage, isLoading, toolActivity, connected } = useChat('Coach')
  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, toolActivity])

  useEffect(() => {
    if (!isLoading && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isLoading])

  const handleSend = (text) => {
    const content = text || input
    if (!content.trim() || isLoading) return
    sendMessage(content)
    setInput('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="bg-navy-800 border border-navy-600 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-navy-700">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center">
            <svg className="w-4 h-4 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3" />
              <path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
            </svg>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-200">Trading Coach</h4>
            <div className="flex items-center gap-1.5">
              <div className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-positive' : 'bg-negative'}`} />
              <span className="text-xs text-slate-500">{connected ? 'Online' : 'Connecting...'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="h-96 overflow-y-auto px-5 py-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-sm text-slate-500 mb-4">Ask me about your trading patterns and how to improve.</p>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTED_QUESTIONS.slice(0, 4).map((question, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(question)}
                  disabled={isLoading}
                  className="px-3 py-1.5 bg-navy-700/50 hover:bg-navy-700 border border-navy-600 hover:border-accent/30 rounded-full text-xs text-slate-400 hover:text-slate-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <CoachMessage key={message.id} message={message} />
          ))
        )}

        {/* Tool activity indicator */}
        {toolActivity && (
          <div className="flex justify-start">
            <div className="bg-navy-700/50 rounded-xl px-4 py-3">
              <div className="flex items-center gap-2">
                <svg className="w-3 h-3 text-accent animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" strokeDasharray="32" strokeLinecap="round" />
                </svg>
                <span className="text-xs text-slate-500">
                  {toolActivity.status === 'calling' ? `Analyzing with ${toolActivity.tool}...` : `${toolActivity.tool} complete`}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Typing indicator */}
        {isLoading && !toolActivity && (
          <div className="flex justify-start">
            <div className="bg-navy-700/50 rounded-xl px-4 py-3">
              <div className="flex items-center gap-1">
                <div className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested questions (shown when there are messages) */}
      {messages.length > 0 && messages.length < 6 && (
        <div className="px-5 py-2 border-t border-navy-700/50">
          <div className="flex gap-2 overflow-x-auto pb-1">
            {SUGGESTED_QUESTIONS.filter(q =>
              !messages.some(m => m.content === q)
            ).slice(0, 3).map((question, i) => (
              <button
                key={i}
                onClick={() => handleSend(question)}
                disabled={isLoading}
                className="flex-shrink-0 px-3 py-1 bg-navy-700/30 hover:bg-navy-700 border border-navy-600/50 rounded-full text-xs text-slate-500 hover:text-slate-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="px-5 py-3 border-t border-navy-700">
        <div className="flex items-end gap-3">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your trading patterns..."
            disabled={isLoading}
            rows={1}
            className="flex-1 bg-navy-700 border border-navy-600 rounded-xl px-4 py-2.5 text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-accent/50 resize-none max-h-24"
            style={{ minHeight: '40px' }}
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className={`flex items-center justify-center w-10 h-10 rounded-xl transition-all ${
              input.trim() && !isLoading
                ? 'bg-accent text-navy-900 hover:bg-accent-light'
                : 'bg-navy-700 text-slate-500 cursor-not-allowed'
            }`}
          >
            {isLoading ? (
              <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeDasharray="32" strokeLinecap="round" />
              </svg>
            ) : (
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

function CoachMessage({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[85%] rounded-xl px-4 py-3 ${
        isUser
          ? 'bg-accent/10 border border-accent/20'
          : 'bg-navy-700/50'
      }`}>
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-xs font-medium ${isUser ? 'text-accent' : 'text-slate-400'}`}>
            {isUser ? 'You' : 'Coach'}
          </span>
          {message.timestamp && (
            <span className="text-xs text-slate-600">{formatTimestamp(message.timestamp)}</span>
          )}
        </div>
        <div className={`text-sm leading-relaxed ${isUser ? 'text-slate-200' : 'text-slate-300'}`}>
          <FormattedContent content={message.content} />
        </div>
      </div>
    </div>
  )
}

function FormattedContent({ content }) {
  if (!content) return null

  const paragraphs = content.split('\n\n')

  return (
    <div className="space-y-2">
      {paragraphs.map((paragraph, i) => {
        const lines = paragraph.split('\n')
        const isList = lines.every(line =>
          line.trim().startsWith('-') || line.trim().startsWith('*') || /^\d+\./.test(line.trim())
        )

        if (isList) {
          return (
            <ul key={i} className="space-y-1 ml-1">
              {lines.map((line, j) => (
                <li key={j} className="flex items-start gap-2">
                  <span className="text-accent mt-1 text-xs">*</span>
                  <span>{line.replace(/^[-*]\s*/, '').replace(/^\d+\.\s*/, '')}</span>
                </li>
              ))}
            </ul>
          )
        }

        // Handle bold text
        const parts = paragraph.split(/(\*\*[^*]+\*\*)/g)
        return (
          <p key={i}>
            {parts.map((part, j) => {
              if (part.startsWith('**') && part.endsWith('**')) {
                return <strong key={j} className="font-semibold text-slate-100">{part.slice(2, -2)}</strong>
              }
              return part
            })}
          </p>
        )
      })}
    </div>
  )
}
