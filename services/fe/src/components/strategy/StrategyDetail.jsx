import { useState, useEffect } from 'react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import Card, { CardHeader } from '../common/Card'
import ConditionBadge from './ConditionBadge'
import { formatINR } from '../../utils/formatters'
import { useApi } from '../../hooks/useApi'
import { getPrice } from '../../api/market'

export default function StrategyDetail({ strategy, onToggle, onDelete }) {
  const [conditionStatus, setConditionStatus] = useState({})
  const isActive = strategy.status === 'active'
  const stats = strategy.paperTradingStats || {}

  const { data: spotData } = useApi(() => getPrice('NIFTY 50'), [], { skip: !isActive })

  // Simulate condition checking for active strategies
  useEffect(() => {
    if (!isActive) return

    const checkConditions = () => {
      const status = {}
      strategy.entryConditions?.forEach((cond, idx) => {
        // Simulate condition evaluation
        status[`cond_${idx}`] = Math.random() > 0.4 // 60% chance of being met
      })
      setConditionStatus(status)
    }

    checkConditions()
    const interval = setInterval(checkConditions, 5000)
    return () => clearInterval(interval)
  }, [isActive, strategy.entryConditions])

  // Generate mock P&L chart data
  const pnlChartData = generatePnlChartData(stats.trades || [])

  const allConditionsMet = Object.values(conditionStatus).every(v => v)

  const spotPrice = spotData?.price || 0

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card>
        <div className="flex items-start justify-between mb-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-2xl">
                {strategy.action?.type === 'BUY' ? '📈' : '📉'}
              </span>
              <h2 className="text-xl font-bold text-slate-100">{strategy.name}</h2>
              <StatusBadge status={strategy.status} />
            </div>
            <p className="text-slate-400">{strategy.description}</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onToggle}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                isActive
                  ? 'bg-yellow-500/10 text-yellow-400 hover:bg-yellow-500/20'
                  : 'bg-positive/10 text-positive hover:bg-positive/20'
              }`}
            >
              {isActive ? 'Pause Strategy' : 'Activate Strategy'}
            </button>
            <button
              onClick={onDelete}
              className="px-4 py-2 text-sm font-medium text-negative bg-negative/10 hover:bg-negative/20 rounded-lg transition-colors"
            >
              Delete
            </button>
          </div>
        </div>

        {/* Original Input */}
        <div className="bg-navy-700/50 rounded-lg p-4 mb-6">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">
            Original Strategy Input
          </div>
          <p className="text-slate-300 italic">"{strategy.naturalLanguageInput || strategy.originalInput}"</p>
        </div>

        {/* Entry Conditions */}
        <div className="mb-6">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-3">
            Entry Conditions
          </div>
          <div className="flex flex-wrap gap-2">
            {strategy.entryConditions?.map((condition, idx) => (
              <div key={idx} className="relative">
                <ConditionBadge condition={condition} type="entry" />
                {isActive && (
                  <span className={`absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-navy-800 ${
                    conditionStatus[`cond_${idx}`] ? 'bg-positive' : 'bg-slate-500'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Action */}
        <div className="mb-6">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-3">
            Action
          </div>
          <div className="flex items-center gap-3">
            <span className={`px-3 py-1.5 rounded-lg text-sm font-semibold ${
              strategy.action?.type === 'BUY'
                ? 'bg-positive/20 text-positive'
                : 'bg-negative/20 text-negative'
            }`}>
              {strategy.action?.type}
            </span>
            <span className="text-slate-200 font-medium">
              {strategy.action?.quantity} lot{strategy.action?.quantity > 1 ? 's' : ''}
            </span>
            <span className="text-slate-300">
              {strategy.action?.instrument} {strategy.action?.strikeSelection} {strategy.action?.optionType}
            </span>
          </div>
        </div>

        {/* Exit Conditions */}
        <div>
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-3">
            Exit Conditions
          </div>
          <div className="flex flex-wrap gap-2">
            {strategy.exitConditions?.map((condition, idx) => (
              <ConditionBadge key={idx} condition={condition} type="exit" />
            ))}
          </div>
        </div>
      </Card>

      {/* Live Status Card (only for active strategies) */}
      {isActive && (
        <Card className="border-2 border-accent/30">
          <CardHeader
            title="Live Status"
            subtitle="Real-time condition monitoring"
          />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-navy-700/50 rounded-lg p-3">
              <div className="text-xs text-slate-500 mb-1">{strategy.action?.instrument} Spot</div>
              <div className="text-lg font-semibold text-slate-200">
                ₹{spotPrice.toLocaleString('en-IN')}
              </div>
            </div>
            <div className="bg-navy-700/50 rounded-lg p-3">
              <div className="text-xs text-slate-500 mb-1">Day's Low</div>
              <div className="text-lg font-semibold text-slate-200">
                ₹{(spotPrice - 85).toLocaleString('en-IN')}
              </div>
            </div>
            <div className="bg-navy-700/50 rounded-lg p-3">
              <div className="text-xs text-slate-500 mb-1">Distance from Low</div>
              <div className="text-lg font-semibold text-positive">+85 pts</div>
            </div>
            <div className="bg-navy-700/50 rounded-lg p-3">
              <div className="text-xs text-slate-500 mb-1">OI Change</div>
              <div className="text-lg font-semibold text-positive">+2.3%</div>
            </div>
          </div>

          <div className={`flex items-center gap-3 p-4 rounded-lg ${
            allConditionsMet
              ? 'bg-positive/10 border border-positive/30'
              : 'bg-navy-700/50'
          }`}>
            {allConditionsMet ? (
              <>
                <span className="text-2xl">⚡</span>
                <div>
                  <div className="font-semibold text-positive">All Conditions Met!</div>
                  <div className="text-sm text-slate-400">Waiting for execution window...</div>
                </div>
              </>
            ) : (
              <>
                <span className="text-2xl">⏳</span>
                <div>
                  <div className="font-medium text-slate-300">Monitoring Conditions</div>
                  <div className="text-sm text-slate-500">
                    {Object.values(conditionStatus).filter(v => v).length} of {strategy.entryConditions?.length || 0} conditions met
                  </div>
                </div>
              </>
            )}
          </div>
        </Card>
      )}

      {/* Performance Card */}
      <Card>
        <CardHeader
          title="Paper Trading Performance"
          subtitle="Simulated results based on historical data"
        />

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <StatBox
            label="Total P&L"
            value={formatINR(stats.totalPnl || 0, true)}
            color={stats.totalPnl >= 0 ? 'positive' : 'negative'}
          />
          <StatBox
            label="Win Rate"
            value={`${stats.winRate || 0}%`}
            color={stats.winRate >= 50 ? 'positive' : 'negative'}
          />
          <StatBox
            label="Total Trades"
            value={stats.totalTrades || 0}
          />
          <StatBox
            label="Avg Trade"
            value={formatINR(stats.totalTrades ? (stats.totalPnl / stats.totalTrades) : 0, true)}
            color={stats.totalPnl >= 0 ? 'positive' : 'negative'}
          />
        </div>

        {/* P&L Chart */}
        {pnlChartData.length > 0 && (
          <div className="h-48 mb-6">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={pnlChartData}>
                <defs>
                  <linearGradient id="pnlGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="date"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#64748b', fontSize: 11 }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#64748b', fontSize: 11 }}
                  tickFormatter={(v) => `₹${v/1000}k`}
                />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine y={0} stroke="#475569" strokeDasharray="3 3" />
                <Area
                  type="monotone"
                  dataKey="cumPnl"
                  stroke="#10B981"
                  fill="url(#pnlGradient)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Trade History */}
        <div>
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-3">
            Recent Trades
          </div>
          {stats.trades && stats.trades.length > 0 ? (
            <div className="space-y-2">
              {stats.trades.slice(0, 5).map((trade, idx) => (
                <TradeRow key={idx} trade={trade} />
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">
              No trades executed yet. Activate the strategy to start paper trading.
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}

function StatBox({ label, value, color }) {
  const colorClass = color === 'positive'
    ? 'text-positive'
    : color === 'negative'
      ? 'text-negative'
      : 'text-slate-200'

  return (
    <div className="bg-navy-700/50 rounded-lg p-4">
      <div className="text-xs text-slate-500 mb-1">{label}</div>
      <div className={`text-xl font-bold ${colorClass}`}>{value}</div>
    </div>
  )
}

function StatusBadge({ status }) {
  const config = {
    active: { bg: 'bg-positive/20', text: 'text-positive', dot: 'bg-positive', label: 'Active' },
    paused: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', dot: 'bg-yellow-400', label: 'Paused' },
    stopped: { bg: 'bg-slate-500/20', text: 'text-slate-400', dot: 'bg-slate-400', label: 'Stopped' }
  }

  const { bg, text, dot, label } = config[status] || config.paused

  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${bg} ${text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dot} ${status === 'active' ? 'animate-pulse' : ''}`} />
      {label}
    </span>
  )
}

function TradeRow({ trade }) {
  const isWin = trade.pnl >= 0
  return (
    <div className="flex items-center justify-between py-2 px-3 bg-navy-700/30 rounded-lg">
      <div className="flex items-center gap-3">
        <span className={`w-2 h-2 rounded-full ${isWin ? 'bg-positive' : 'bg-negative'}`} />
        <span className="text-sm text-slate-300">{trade.date}</span>
      </div>
      <div className="flex items-center gap-4 text-sm">
        <span className="text-slate-400">Entry: ₹{trade.entry}</span>
        <span className="text-slate-400">Exit: ₹{trade.exit}</span>
        <span className={`font-semibold ${isWin ? 'text-positive' : 'text-negative'}`}>
          {formatINR(trade.pnl, true)}
        </span>
        <span className={`text-xs px-2 py-0.5 rounded ${
          isWin ? 'bg-positive/10 text-positive' : 'bg-negative/10 text-negative'
        }`}>
          {trade.exitReason}
        </span>
      </div>
    </div>
  )
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null

  return (
    <div className="bg-navy-700 border border-navy-600 rounded-lg px-3 py-2 shadow-lg">
      <div className="text-xs text-slate-400 mb-1">{label}</div>
      <div className={`font-semibold ${payload[0].value >= 0 ? 'text-positive' : 'text-negative'}`}>
        {formatINR(payload[0].value, true)}
      </div>
    </div>
  )
}

function generatePnlChartData(trades) {
  if (!trades || trades.length === 0) {
    // Generate mock data for demo
    const mockData = []
    let cumPnl = 0
    for (let i = 0; i < 15; i++) {
      const date = new Date()
      date.setDate(date.getDate() - (14 - i))
      const pnl = (Math.random() - 0.4) * 3000 // Slightly positive bias
      cumPnl += pnl
      mockData.push({
        date: date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }),
        pnl: Math.round(pnl),
        cumPnl: Math.round(cumPnl)
      })
    }
    return mockData
  }

  let cumPnl = 0
  return trades.map(trade => {
    cumPnl += trade.pnl
    return {
      date: trade.date,
      pnl: trade.pnl,
      cumPnl
    }
  })
}
