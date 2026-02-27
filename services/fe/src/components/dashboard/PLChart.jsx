import { useMemo, memo } from 'react'
import { XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, Area, AreaChart } from 'recharts'
import { formatINR, formatTime } from '../../utils/formatters'
import Card, { CardHeader } from '../common/Card'

function PLChart({ data, currentPnl }) {
  if (!data || data.length === 0) return null

  // Transform API shape {total_value, cash, invested_value, timestamp} → {pnl, time}
  const chartData = useMemo(() => {
    const baseline = data[0]?.total_value ?? 0
    const historicalData = data.map(d => ({
      pnl: (d.pnl != null ? d.pnl : (d.total_value != null ? d.total_value - baseline : 0)),
      time: d.time || (d.timestamp ? formatTime(d.timestamp) : ''),
    }))

    // Append current real-time P&L as the latest data point
    if (currentPnl != null) {
      const now = new Date()
      const currentTime = now.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      })

      // Check if we already have a data point for this minute
      const lastDataPoint = historicalData[historicalData.length - 1]
      if (lastDataPoint && lastDataPoint.time === currentTime) {
        // Update the last data point with current P&L
        lastDataPoint.pnl = currentPnl
      } else {
        // Add new data point
        historicalData.push({
          pnl: currentPnl,
          time: currentTime,
        })
      }
    }

    return historicalData
  }, [data, currentPnl])

  const latestPnl = chartData[chartData.length - 1]?.pnl || 0
  const maxPnl = Math.max(...chartData.map(d => d.pnl))
  const minPnl = Math.min(...chartData.map(d => d.pnl))

  const isPositive = latestPnl >= 0
  const strokeColor = isPositive ? '#34D399' : '#F87171'
  const gradientId = 'pnlGradient'

  // Symmetric domain for balanced chart
  const absMax = Math.max(Math.abs(maxPnl), Math.abs(minPnl), 1000)
  const domainPadding = absMax * 0.1
  const yDomain = [Math.min(minPnl, 0) - domainPadding, Math.max(maxPnl, 0) + domainPadding]

  return (
    <Card>
      <CardHeader
        title="P&L Timeline"
        subtitle="Intraday profit & loss"
        action={
          <div className="text-right">
            <div className="text-xs text-slate-500">Current</div>
            <div className={`font-mono text-lg font-semibold ${isPositive ? 'text-positive' : 'text-negative'}`}>
              {formatINR(latestPnl, true)}
            </div>
          </div>
        }
      />

      {/* Summary stats */}
      <div className="flex items-center gap-6 mb-4">
        <div>
          <span className="text-xs text-slate-500">Peak </span>
          <span className="text-xs font-mono text-positive">{formatINR(maxPnl, true)}</span>
        </div>
        <div>
          <span className="text-xs text-slate-500">Trough </span>
          <span className="text-xs font-mono text-negative">{formatINR(minPnl, true)}</span>
        </div>
        <div>
          <span className="text-xs text-slate-500">Range </span>
          <span className="text-xs font-mono text-slate-300">{formatINR(maxPnl - minPnl)}</span>
        </div>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={strokeColor} stopOpacity={0.3} />
                <stop offset="95%" stopColor={strokeColor} stopOpacity={0} />
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
              tickFormatter={(value) => {
                const abs = Math.abs(value)
                if (abs >= 100000) return `${value < 0 ? '-' : ''}${(abs / 100000).toFixed(1)}L`
                if (abs >= 1000) return `${value < 0 ? '-' : ''}${(abs / 1000).toFixed(0)}K`
                return `${value}`
              }}
              dx={-10}
              domain={yDomain}
            />

            <Tooltip content={<CustomTooltip />} />

            <ReferenceLine y={0} stroke="#1A2942" strokeWidth={1} />

            <Area
              type="monotone"
              dataKey="pnl"
              stroke={strokeColor}
              strokeWidth={2}
              fill={`url(#${gradientId})`}
              dot={false}
              activeDot={{ r: 4, fill: strokeColor, stroke: '#0F172A', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null

  const pnl = payload[0].value
  const isPositive = pnl >= 0

  return (
    <div className="bg-navy-700 border border-navy-600 rounded-lg px-3 py-2 shadow-lg">
      <div className="text-xs text-slate-400 mb-1">{label}</div>
      <div className={`font-mono font-semibold ${isPositive ? 'text-positive' : 'text-negative'}`}>
        {formatINR(pnl, true)}
      </div>
    </div>
  )
}

// Memoize to only re-render when data or currentPnl changes
export default memo(PLChart)
