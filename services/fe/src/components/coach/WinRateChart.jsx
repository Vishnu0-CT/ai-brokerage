import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts'
import Card, { CardHeader } from '../common/Card'

export default function WinRateChart({ data, title, subtitle }) {
  if (!data || data.length === 0) return null

  return (
    <Card>
      <CardHeader title={title} subtitle={subtitle} />

      <div className="h-64 mt-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <XAxis
              dataKey="label"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748B', fontSize: 11 }}
              dy={10}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748B', fontSize: 11 }}
              tickFormatter={(value) => `${value}%`}
              dx={-10}
              domain={[0, 100]}
            />

            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(56, 189, 248, 0.1)' }} />

            <ReferenceLine y={50} stroke="#1A2942" strokeDasharray="3 3" />

            <Bar dataKey="winRate" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.winRate >= 50 ? '#34D399' : '#F87171'}
                  fillOpacity={0.8}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t border-navy-700">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-positive" />
          <span className="text-xs text-slate-500">Above 50%</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-negative" />
          <span className="text-xs text-slate-500">Below 50%</span>
        </div>
      </div>
    </Card>
  )
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null

  const data = payload[0].payload
  const isGood = data.winRate >= 50

  return (
    <div className="bg-navy-700 border border-navy-600 rounded-lg px-3 py-2 shadow-lg">
      <div className="text-xs text-slate-400 mb-1">{label}</div>
      <div className={`font-mono font-semibold ${isGood ? 'text-positive' : 'text-negative'}`}>
        {data.winRate.toFixed(1)}% win rate
      </div>
      <div className="text-xs text-slate-500 mt-1">{data.trades} trades</div>
      {data.pnl !== undefined && (
        <div className={`text-xs font-mono mt-1 ${data.pnl >= 0 ? 'text-positive' : 'text-negative'}`}>
          \u20b9{data.pnl.toLocaleString('en-IN')}
        </div>
      )}
    </div>
  )
}
