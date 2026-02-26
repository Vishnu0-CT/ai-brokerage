const suggestions = [
  { text: "What's my biggest risk right now?", icon: '\u26a0\ufe0f' },
  { text: "Show me my P&L breakdown", icon: '\ud83d\udcca' },
  { text: "What if Nifty falls 200 points?", icon: '\ud83d\udcc9' },
  { text: "How much margin will I free up if I exit HDFC PE?", icon: '\ud83d\udcb0' },
  { text: "What's my net delta exposure?", icon: '\ud83d\udcc8' },
  { text: "Show me my worst performing position", icon: '\ud83d\udd34' },
]

export default function SuggestedQueries({ onSelect, disabled }) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-500">Try asking:</p>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((suggestion, i) => (
          <button
            key={i}
            onClick={() => onSelect(suggestion.text)}
            disabled={disabled}
            className="flex items-center gap-2 px-4 py-2 bg-navy-700/50 hover:bg-navy-700 border border-navy-600 hover:border-accent/30 rounded-full text-sm text-slate-300 hover:text-slate-100 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span>{suggestion.icon}</span>
            <span>{suggestion.text}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
