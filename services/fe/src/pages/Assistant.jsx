import { useChat } from '../hooks/useChat'
import ChatContainer from '../components/assistant/ChatContainer'

export default function Assistant() {
  const { messages, sendMessage, isLoading, toolActivity, connected } = useChat('Assistant')

  return (
    <div className="h-[calc(100vh-64px-48px)] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">AI Assistant</h1>
          <p className="text-sm text-slate-500 mt-1">Natural language interface to your trading portfolio</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-navy-700/50 rounded-full">
          <div className={`w-2 h-2 rounded-full ${connected ? 'bg-positive' : 'bg-negative'} pulse-live`} />
          <span className="text-xs text-slate-400">{connected ? 'Connected' : 'Connecting...'}</span>
        </div>
      </div>
      <div className="flex-1 bg-navy-800/30 rounded-2xl border border-navy-700 overflow-hidden">
        <ChatContainer messages={messages} onSend={sendMessage} isLoading={isLoading} toolActivity={toolActivity} />
      </div>
    </div>
  )
}
