import { memo } from 'react'
import { formatINR } from '../../utils/formatters'

const insightIcons = {
  TIME_ANALYSIS: (
    <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" strokeLinecap="round" />
    </svg>
  ),
  HOLD_TIME: (
    <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="13" r="8" /><path d="M12 9v4l2 2" strokeLinecap="round" /><path d="M5 3L2 6M22 6l-3-3" strokeLinecap="round" />
    </svg>
  ),
  INSTRUMENT: (
    <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M18 20V10M12 20V4M6 20v-6" strokeLinecap="round" />
    </svg>
  ),
  DAY_ANALYSIS: (
    <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" strokeLinecap="round" />
    </svg>
  ),
  PATTERN: (
    <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="6" /><circle cx="12" cy="12" r="2" />
    </svg>
  ),
  WARNING: (
    <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" /><path d="M12 9v4M12 17h.01" strokeLinecap="round" />
    </svg>
  ),
  SUCCESS: (
    <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><path d="M22 4L12 14.01l-3-3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
}

const defaultIcon = (
  <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M9 18h6M10 22h4M12 2a7 7 0 0 1 4 12.7V17H8v-2.3A7 7 0 0 1 12 2z" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
)

function InsightCard({ insight }) {
  const icon = insightIcons[insight.category] || defaultIcon
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
                <svg className="w-4 h-4 text-accent flex-shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 18h6M10 22h4M12 2a7 7 0 0 1 4 12.7V17H8v-2.3A7 7 0 0 1 12 2z" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <p className="text-sm text-accent/90">{insight.recommendation}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Memoize to prevent unnecessary re-renders
export default memo(InsightCard)
