import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts'
import { formatINR } from '../../utils/formatters'
import Card, { CardHeader } from '../common/Card'

export default function WeeklyPLChart({ data }) {
  if (!data || data.length === 0) return null

  const totalPnl = data.reduce((sum, d) => sum + d.pnl, 0)
  const totalTrades = data.reduce((sum, d) => sum + d.trades, 0)

  const winDays = data.filter(d => d.pnl > 0).length
  const lossDays = data.filter(d => d.pnl < 0).length

  const isPositive = totalPnl >= 0

  // Y-axis domain with padding
  const maxAbs = Math.max(...data.map(d => Math.abs(d.pnl)), 1000)
  const domainPadding = maxAbs * 0.15
  const yDomain = [-(maxAbs + domainPadding), maxAbs + domainPadding]

  return (
    <Card>
      <CardHeader
        title="Weekly P&L"
        subtitle={`${totalTrades} trades this week`}
        action={
          <div className="text-right">
            <div className="text-xs text-slate-500">Week Total</div>
            <div className={`font-mono text-lg font-semibold ${isPositive ? 'text-positive' : 'text-negative'}`}>
              {formatINR(totalPnl, true)}
            </div>
          </div>
        }
      />

      <div className="h-64 mt-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <XAxis
              dataKey="day"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748B', fontSize: 11 }}
              dy={10}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748B', fontSize: 10 }}
              tickFormatter={(value) => {
                const abs = Math.abs(value)
                if (abs >= 100000) return `${value < 0 ? '-' : ''}${(abs / 100000).toFixed(1)}L`
                if (abs >= 1000) return `${value < 0 ? '-' : ''}${(abs / 1000).toFixed(0)}K`
                return `${value}`
              }}
              dx={-10}
              domain={yDomain}
            />

            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(56, 189, 248, 0.05)' }} />

            <ReferenceLine y={0} stroke="#1A2942" strokeWidth={1} />

            <Bar dataKey="pnl" radius={[4, 4, 4, 4]} maxBarSize={40}>
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.pnl >= 0 ? '#34D399' : '#F87171'}
                  fillOpacity={0.8}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend / summary */}
      <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t border-navy-700">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-positive" />
          <span className="text-xs text-slate-500">{winDays} winning {winDays === 1 ? 'day' : 'days'}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-negative" />
          <span className="text-xs text-slate-500">{lossDays} losing {lossDays === 1 ? 'day' : 'days'}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">Avg:</span>
          <span className={`text-xs font-mono ${isPositive ? 'text-positive' : 'text-negative'}`}>
            {formatINR(data.length > 0 ? totalPnl / data.length : 0, true)}/day
          </span>
        </div>
      </div>
    </Card>
  )
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null

  const entry = payload[0].payload
  const isPositive = entry.pnl >= 0

  return (
    <div className="bg-navy-700 border border-navy-600 rounded-lg px-3 py-2 shadow-lg">
      <div className="text-xs text-slate-400 mb-1">{label}</div>
      <div className={`font-mono font-semibold ${isPositive ? 'text-positive' : 'text-negative'}`}>
        {formatINR(entry.pnl, true)}
      </div>
      <div className="text-xs text-slate-500 mt-1">{entry.trades} trades</div>
    </div>
  )
}
