import { formatTimestamp } from '../../utils/formatters'

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'
  const isError = message.isError

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} message-enter`}>
      <div
        className={`max-w-[80%] rounded-2xl px-5 py-4 ${
          isUser
            ? 'bg-accent/20 border border-accent/30'
            : isError
            ? 'bg-negative/10 border border-negative/30'
            : 'bg-navy-700 border border-navy-600'
        }`}
      >
        {/* Header */}
        <div className="flex items-center gap-2 mb-2">
          {!isUser && (
            <div className="w-6 h-6 rounded-full bg-accent/20 flex items-center justify-center">
              <svg className="w-4 h-4 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="3" />
                <path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
              </svg>
            </div>
          )}
          <span className={`text-xs font-medium ${isUser ? 'text-accent' : 'text-slate-400'}`}>
            {isUser ? 'You' : 'ClearTrade'}
          </span>
          <span className="text-xs text-slate-500">
            {formatTimestamp(message.timestamp)}
          </span>
        </div>

        {/* Content */}
        <div className={`text-sm leading-relaxed ${isUser ? 'text-slate-200' : 'text-slate-300'}`}>
          <MessageContent content={message.content} />
        </div>
      </div>
    </div>
  )
}

function MessageContent({ content }) {
  const paragraphs = content.split('\n\n')

  return (
    <div className="space-y-3">
      {paragraphs.map((paragraph, i) => (
        <Paragraph key={i} text={paragraph} />
      ))}
    </div>
  )
}

function Paragraph({ text }) {
  const lines = text.split('\n')
  const isList = lines.every(line => line.trim().startsWith('-') || line.trim().startsWith('\u2022') || /^\d+\./.test(line.trim()))

  if (isList) {
    return (
      <ul className="space-y-1.5 ml-1">
        {lines.map((line, i) => (
          <li key={i} className="flex items-start gap-2">
            <span className="text-accent mt-1.5 text-xs">\u2022</span>
            <span><InlineFormatting text={line.replace(/^[-\u2022]\s*/, '').replace(/^\d+\.\s*/, '')} /></span>
          </li>
        ))}
      </ul>
    )
  }

  if (text.startsWith('**') && text.includes(':**')) {
    const [heading, ...rest] = text.split(':**')
    return (
      <div>
        <span className="font-semibold text-slate-100">{heading.replace(/\*\*/g, '')}:</span>
        <span><InlineFormatting text={rest.join(':**')} /></span>
      </div>
    )
  }

  return <p><InlineFormatting text={text} /></p>
}

function InlineFormatting({ text }) {
  const parts = text.split(/(\*\*[^*]+\*\*|\u20b9[\d,]+|[+-]\u20b9[\d,]+|\+\d+%|-\d+%)/g)

  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={i} className="font-semibold text-slate-100">{part.slice(2, -2)}</strong>
        }
        if (part.match(/^[+-]?\u20b9[\d,]+$/)) {
          const isPositive = part.startsWith('+') || (!part.startsWith('-') && !part.includes('-'))
          const isNegative = part.startsWith('-') || part.includes('\u2013')
          return (
            <span
              key={i}
              className={`font-mono font-medium ${
                isNegative ? 'text-negative' : isPositive && part.startsWith('+') ? 'text-positive' : 'text-slate-200'
              }`}
            >
              {part}
            </span>
          )
        }
        if (part.match(/^[+-]\d+%$/)) {
          const isPositive = part.startsWith('+')
          return (
            <span key={i} className={`font-mono font-medium ${isPositive ? 'text-positive' : 'text-negative'}`}>
              {part}
            </span>
          )
        }
        return part
      })}
    </>
  )
}
