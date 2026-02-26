import { formatINR } from '../../utils/formatters'
import Card, { CardHeader } from '../common/Card'

export default function InstrumentBreakdown({ data }) {
  if (!data || data.length === 0) return null

  const sorted = [...data].sort((a, b) => b.avgPnl - a.avgPnl)
  const maxPnl = Math.max(...data.map(d => Math.abs(d.avgPnl)))

  return (
    <Card>
      <CardHeader
        title="Performance by Instrument"
        subtitle="Average P&L per trade"
      />

      <div className="space-y-4 mt-4">
        {sorted.map((item, index) => {
          const isPositive = item.avgPnl >= 0
          const barWidth = (Math.abs(item.avgPnl) / maxPnl) * 100

          return (
            <div key={item.instrument} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={`w-6 h-6 rounded flex items-center justify-center text-xs font-semibold ${
                    index === 0 ? 'bg-positive/20 text-positive' :
                    index === sorted.length - 1 ? 'bg-negative/20 text-negative' :
                    'bg-navy-700 text-slate-400'
                  }`}>
                    {index + 1}
                  </span>
                  <span className="text-sm font-medium text-slate-200">{item.instrument}</span>
                </div>
                <div className="text-right">
                  <div className={`font-mono text-sm font-semibold ${isPositive ? 'text-positive' : 'text-negative'}`}>
                    {formatINR(item.avgPnl, true)}
                  </div>
                  <div className="text-xs text-slate-500">
                    {item.winRate.toFixed(0)}% win \u2022 {item.trades} trades
                  </div>
                </div>
              </div>

              <div className="h-2 bg-navy-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${isPositive ? 'bg-positive' : 'bg-negative'}`}
                  style={{ width: `${barWidth}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </Card>
  )
}
