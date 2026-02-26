import { getSeverityColors, timeAgo } from '../../utils/formatters'

const alertIcons = {
  REVENGE_TRADING: (
    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  OVERTRADING: (
    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  DRAWDOWN_WARNING: (
    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M3 3v18h18" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M21 9l-6 6-4-4-6 6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  CONCENTRATION_RISK: (
    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 2a10 10 0 0 1 0 20" fill="currentColor" fillOpacity="0.3" />
    </svg>
  ),
  TIME_RISK: (
    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 6v6l4 2" strokeLinecap="round" />
    </svg>
  ),
}

export default function AlertCard({ alert, onDismiss }) {
  const colors = getSeverityColors(alert.severity)
  const Icon = alertIcons[alert.type] || alertIcons.OVERTRADING

  return (
    <div className={`${colors.bg} border ${colors.border} rounded-xl p-5 animate-in`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg ${colors.bg} ${colors.text} flex items-center justify-center`}>
            {Icon}
          </div>
          <div>
            <h4 className={`font-semibold ${colors.text}`}>{alert.title}</h4>
            <p className="text-xs text-slate-500">{timeAgo(alert.created_at || alert.timestamp)}</p>
          </div>
        </div>

        <span className={`text-xs font-medium px-2 py-1 rounded ${colors.bg} ${colors.text}`}>
          {alert.severity.toUpperCase()}
        </span>
      </div>

      {/* Description */}
      <p className="text-sm text-slate-300 mb-4 leading-relaxed">
        {alert.description}
      </p>

      {/* Context data */}
      {alert.context && (
        <div className="flex flex-wrap gap-3 mb-4">
          {Object.entries(alert.context).slice(0, 3).map(([key, value]) => (
            <div key={key} className="bg-navy-800/50 rounded-lg px-3 py-2">
              <div className="text-xs text-slate-500 capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</div>
              <div className="font-mono text-sm text-slate-300">
                {typeof value === 'number'
                  ? value.toLocaleString('en-IN')
                  : Array.isArray(value)
                    ? value.length + ' items'
                    : typeof value === 'object' && value !== null
                      ? (value.symbol ? `${value.symbol}: \u20b9${value.pnl?.toLocaleString('en-IN') || 0}` : JSON.stringify(value))
                      : String(value)}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Suggestion */}
      {alert.suggestion && (
        <div className="flex items-start gap-2 p-3 bg-navy-800/30 rounded-lg mb-4">
          <span className="text-accent text-lg">\ud83d\udca1</span>
          <p className="text-sm text-slate-400">{alert.suggestion}</p>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-end gap-3">
        <button
          onClick={() => onDismiss?.(alert.id)}
          className="px-4 py-2 text-sm text-slate-400 hover:text-slate-200 transition-colors"
        >
          Dismiss
        </button>
        <button className="px-4 py-2 text-sm bg-accent/10 text-accent hover:bg-accent/20 rounded-lg transition-colors">
          Take Action
        </button>
      </div>
    </div>
  )
}
