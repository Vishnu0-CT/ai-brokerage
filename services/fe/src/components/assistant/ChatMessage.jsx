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
  const blocks = parseContent(content)

  return (
    <div className="space-y-3">
      {blocks.map((block, i) => (
        <Block key={i} block={block} />
      ))}
    </div>
  )
}

function parseContent(content) {
  const blocks = []
  const lines = content.split('\n')
  let i = 0

  while (i < lines.length) {
    const line = lines[i]

    // Code block
    if (line.trim().startsWith('```')) {
      const language = line.trim().slice(3).trim()
      const codeLines = []
      i++
      while (i < lines.length && !lines[i].trim().startsWith('```')) {
        codeLines.push(lines[i])
        i++
      }
      blocks.push({ type: 'code', language, content: codeLines.join('\n') })
      i++
      continue
    }

    // Heading
    if (line.trim().match(/^#{1,6}\s/)) {
      const level = line.trim().match(/^#+/)[0].length
      const text = line.trim().replace(/^#+\s*/, '')
      blocks.push({ type: 'heading', level, text })
      i++
      continue
    }

    // List
    if (line.trim().match(/^[-*•]\s/) || line.trim().match(/^\d+\.\s/)) {
      const listItems = []
      while (i < lines.length && (lines[i].trim().match(/^[-*•]\s/) || lines[i].trim().match(/^\d+\.\s/))) {
        listItems.push(lines[i].trim().replace(/^[-*•]\s*/, '').replace(/^\d+\.\s*/, ''))
        i++
      }
      blocks.push({ type: 'list', items: listItems })
      continue
    }

    // Paragraph
    if (line.trim()) {
      const paragraphLines = []
      while (i < lines.length && lines[i].trim() && !lines[i].trim().startsWith('```') && !lines[i].trim().match(/^#{1,6}\s/) && !lines[i].trim().match(/^[-*•]\s/) && !lines[i].trim().match(/^\d+\.\s/)) {
        paragraphLines.push(lines[i])
        i++
      }
      blocks.push({ type: 'paragraph', text: paragraphLines.join('\n') })
      continue
    }

    i++
  }

  return blocks
}

function Block({ block }) {
  switch (block.type) {
    case 'code':
      return <CodeBlock language={block.language} content={block.content} />
    case 'heading':
      return <Heading level={block.level} text={block.text} />
    case 'list':
      return <List items={block.items} />
    case 'paragraph':
      return <Paragraph text={block.text} />
    default:
      return null
  }
}

function CodeBlock({ language, content }) {
  return (
    <div className="relative group">
      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={() => navigator.clipboard.writeText(content)}
          className="px-2 py-1 text-xs bg-navy-600 hover:bg-navy-500 text-slate-300 rounded"
        >
          Copy
        </button>
      </div>
      {language && (
        <div className="text-xs text-slate-500 mb-1 font-mono">{language}</div>
      )}
      <pre className="bg-navy-900 border border-navy-600 rounded-lg p-3 overflow-x-auto">
        <code className="text-sm font-mono text-slate-300">{content}</code>
      </pre>
    </div>
  )
}

function Heading({ level, text }) {
  const sizes = {
    1: 'text-xl font-bold',
    2: 'text-lg font-bold',
    3: 'text-base font-semibold',
    4: 'text-base font-semibold',
    5: 'text-sm font-semibold',
    6: 'text-sm font-semibold',
  }
  return (
    <div className={`${sizes[level]} text-slate-100 mt-4 mb-2`}>
      <InlineFormatting text={text} />
    </div>
  )
}

function List({ items }) {
  return (
    <ul className="space-y-1.5 ml-1">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2">
          <span className="text-accent mt-1.5 text-xs">{'\u2022'}</span>
          <span><InlineFormatting text={item} /></span>
        </li>
      ))}
    </ul>
  )
}

function Paragraph({ text }) {
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
