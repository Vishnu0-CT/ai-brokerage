import { formatINR } from '../../utils/formatters'

const insightIcons = {
  TIME_ANALYSIS: '\u23f0',
  HOLD_TIME: '\u23f1\ufe0f',
  INSTRUMENT: '\ud83d\udcca',
  DAY_ANALYSIS: '\ud83d\udcc5',
  PATTERN: '\ud83c\udfaf',
  WARNING: '\u26a0\ufe0f',
  SUCCESS: '\u2705',
}

export default function InsightCard({ insight }) {
  const icon = insightIcons[insight.category] || '\ud83d\udca1'
  const isPositive = insight.impact >= 0

  return (
    <div className="bg-navy-800 border border-navy-600 rounded-xl p-5 hover:border-accent/30 transition-colors">
      <div className="flex items-start gap-4">
        <div className="text-2xl">{icon}</div>

        <div className="flex-1">
          <h4 className="font-semibold text-slate-200 mb-2">{insight.title}</h4>
          <p className="text-sm text-slate-400 leading-relaxed mb-3">
            {insight.insight}
          </p>

          {insight.impact !== undefined && (
            <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg ${
              isPositive ? 'bg-positive/10' : 'bg-negative/10'
            }`}>
              <span className="text-xs text-slate-500">Monthly Impact:</span>
              <span className={`font-mono text-sm font-semibold ${isPositive ? 'text-positive' : 'text-negative'}`}>
                {formatINR(insight.impact, true)}
              </span>
            </div>
          )}

          {insight.recommendation && (
            <div className="mt-3 p-3 bg-accent/5 border border-accent/20 rounded-lg">
              <div className="flex items-start gap-2">
                <span className="text-accent">\ud83d\udca1</span>
                <p className="text-sm text-accent/90">{insight.recommendation}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
