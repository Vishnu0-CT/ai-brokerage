import { useRef, useEffect } from 'react'
import ChatMessage from './ChatMessage'
import ChatInput from './ChatInput'
import SuggestedQueries from './SuggestedQueries'

export default function ChatContainer({ messages, onSend, isLoading, toolActivity }) {
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, toolActivity])

  const hasMessages = messages.length > 0

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {!hasMessages ? (
          <EmptyState onSuggestionSelect={onSend} isLoading={isLoading} />
        ) : (
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {toolActivity && <ToolActivityIndicator activity={toolActivity} />}
            {isLoading && !toolActivity && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
      <div className="border-t border-navy-700 p-4 bg-navy-800/50">
        <div className="max-w-3xl mx-auto">
          <ChatInput onSend={onSend} isLoading={isLoading} />
        </div>
      </div>
    </div>
  )
}

function ToolActivityIndicator({ activity }) {
  return (
    <div className="flex justify-start">
      <div className="bg-navy-700 border border-navy-600 rounded-2xl px-5 py-4">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-accent/20 flex items-center justify-center">
            <svg className="w-4 h-4 text-accent animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" strokeDasharray="32" strokeLinecap="round" />
            </svg>
          </div>
          <span className="text-xs font-medium text-slate-400">
            {activity.status === 'calling' ? `Using ${activity.tool}...` : `${activity.tool} complete`}
          </span>
        </div>
      </div>
    </div>
  )
}

function EmptyState({ onSuggestionSelect, isLoading }) {
  return (
    <div className="flex flex-col items-center justify-center h-full max-w-lg mx-auto text-center">
      {/* AI Icon */}
      <div className="w-20 h-20 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center mb-6">
        <svg className="w-10 h-10 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="12" cy="12" r="3" />
          <path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
          <path d="M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
        </svg>
      </div>

      <h2 className="text-xl font-semibold text-slate-200 mb-2">ClearTrade Assistant</h2>
      <p className="text-sm text-slate-400 mb-8 leading-relaxed">
        Ask me anything about your portfolio, risk exposure, trade history, or market conditions.
        I can analyze positions, simulate scenarios, and provide actionable insights.
      </p>

      <SuggestedQueries onSelect={onSuggestionSelect} disabled={isLoading} />
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="bg-navy-700 border border-navy-600 rounded-2xl px-5 py-4">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-accent/20 flex items-center justify-center">
            <svg className="w-4 h-4 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3" />
              <path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
            </svg>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      </div>
    </div>
  )
}
