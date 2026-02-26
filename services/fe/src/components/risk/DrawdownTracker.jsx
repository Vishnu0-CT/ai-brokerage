import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { formatINR } from '../../utils/formatters'
import Card, { CardHeader } from '../common/Card'

export default function DrawdownTracker({ historyData, dailyLossLimit = 25000 }) {
  if (!historyData || historyData.length === 0) return null

  // Calculate drawdown at each point
  const drawdownData = historyData.map((point, index) => {
    const maxPnlSoFar = Math.max(...historyData.slice(0, index + 1).map(p => p.pnl))
    const drawdown = point.pnl - maxPnlSoFar
    return {
      ...point,
      drawdown: Math.min(0, drawdown),
    }
  })

  const currentDrawdown = drawdownData[drawdownData.length - 1]?.drawdown || 0
  const maxDrawdown = Math.min(...drawdownData.map(d => d.drawdown))
  const limitUsed = (Math.abs(maxDrawdown) / dailyLossLimit) * 100

  return (
    <Card>
      <CardHeader
        title="Drawdown Tracker"
        subtitle="Intraday drawdown from peak"
        action={
          <div className="text-right">
            <div className="text-xs text-slate-500">Max Drawdown</div>
            <div className="font-mono text-lg font-semibold text-negative">
              {formatINR(maxDrawdown)}
            </div>
          </div>
        }
      />

      <div className="h-48 mt-4">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={drawdownData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#F87171" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#F87171" stopOpacity={0} />
              </linearGradient>
            </defs>

            <XAxis
              dataKey="time"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748B', fontSize: 10 }}
              dy={10}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748B', fontSize: 10 }}
              tickFormatter={(value) => `\u20b9${(value / 1000).toFixed(0)}K`}
              dx={-10}
              domain={[-dailyLossLimit, 0]}
            />

            <Tooltip content={<CustomTooltip />} />

            <ReferenceLine
              y={-dailyLossLimit}
              stroke="#F87171"
              strokeDasharray="5 5"
              label={{ value: 'Loss Limit', fill: '#F87171', fontSize: 10, position: 'right' }}
            />

            <ReferenceLine y={0} stroke="#1A2942" />

            <Area
              type="monotone"
              dataKey="drawdown"
              stroke="#F87171"
              strokeWidth={2}
              fill="url(#drawdownGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Limit usage bar */}
      <div className="mt-4 pt-4 border-t border-navy-700">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-slate-500">Daily Loss Limit Usage</span>
          <span className={`font-mono text-sm ${limitUsed > 75 ? 'text-negative' : limitUsed > 50 ? 'text-warning' : 'text-positive'}`}>
            {limitUsed.toFixed(0)}%
          </span>
        </div>
        <div className="h-2 bg-navy-700 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              limitUsed > 75 ? 'bg-negative' : limitUsed > 50 ? 'bg-warning' : 'bg-positive'
            }`}
            style={{ width: `${Math.min(limitUsed, 100)}%` }}
          />
        </div>
        <div className="flex items-center justify-between mt-2">
          <span className="text-xs text-slate-500">
            Buffer: {formatINR(dailyLossLimit - Math.abs(maxDrawdown))}
          </span>
          <span className="text-xs text-slate-500">
            Limit: {formatINR(dailyLossLimit)}
          </span>
        </div>
      </div>
    </Card>
  )
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null

  const value = payload[0].value

  return (
    <div className="bg-navy-700 border border-navy-600 rounded-lg px-3 py-2 shadow-lg">
      <div className="text-xs text-slate-400 mb-1">{label}</div>
      <div className="font-mono font-semibold text-negative">
        {formatINR(value)}
      </div>
    </div>
  )
}
