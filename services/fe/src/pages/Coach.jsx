import { useApi } from '../hooks/useApi'
import { getCoaching, getWinRateByTime, getInstrumentStats } from '../api/analytics'
import WinRateChart from '../components/coach/WinRateChart'
import InstrumentBreakdown from '../components/coach/InstrumentBreakdown'
import InsightCard from '../components/coach/InsightCard'
import CoachChat from '../components/coach/CoachChat'
import { formatINR, formatPercent, getPnlColor } from '../utils/formatters'
import { CardSkeleton, ChartSkeleton } from '../components/common/Skeleton'
import ErrorMessage from '../components/common/ErrorMessage'
import Card, { CardHeader } from '../components/common/Card'

export default function Coach() {
  const { data: coaching, loading: coachingLoading, error: coachingError, refetch: refetchCoaching } = useApi(() => getCoaching(), [])
  const { data: timeDataRaw, loading: timeLoading } = useApi(() => getWinRateByTime(), [])
  const { data: instrumentData, loading: instrumentLoading } = useApi(() => getInstrumentStats(), [])

  // Transform timeData from object to array format for WinRateChart
  const timeData = timeDataRaw ? Object.entries(timeDataRaw).map(([key, value]) => ({
    label: key.charAt(0).toUpperCase() + key.slice(1),
    winRate: value.win_rate ?? value.winRate ?? 0,
    trades: value.trades ?? 0,
    pnl: value.pnl ?? 0,
  })) : []

  const summary = coaching?.summary || {}
  const insights = coaching?.insights || []
  const holdTimeAnalysis = coaching?.hold_time_analysis || coaching?.holdTimeAnalysis || null

  const winRate = summary.win_rate || summary.winRate || 0
  const totalTrades = summary.total_trades || summary.totalTrades || 0
  const avgWin = summary.avg_win || summary.avgWin || 0
  const avgLoss = summary.avg_loss || summary.avgLoss || 0
  const profitFactor = summary.profit_factor || summary.profitFactor || 0
  const totalPnl = summary.total_pnl || summary.totalPnl || 0

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">Trading Coach</h1>
          <p className="text-sm text-slate-500 mt-1">AI-powered analysis of your trading patterns</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-navy-700/50 rounded-full">
          <div className="w-2 h-2 rounded-full bg-accent pulse-live" />
          <span className="text-xs text-slate-400">Analysis up-to-date</span>
        </div>
      </div>

      {/* Summary Cards */}
      {coachingLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
          <CardSkeleton /><CardSkeleton /><CardSkeleton /><CardSkeleton /><CardSkeleton /><CardSkeleton />
        </div>
      ) : coachingError ? (
        <ErrorMessage error={coachingError} onRetry={refetchCoaching} />
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
          <SummaryCard
            label="Win Rate"
            value={`${winRate.toFixed(1)}%`}
            color={winRate >= 50 ? 'text-positive' : 'text-negative'}
          />
          <SummaryCard
            label="Total Trades"
            value={totalTrades.toLocaleString('en-IN')}
            color="text-slate-200"
          />
          <SummaryCard
            label="Avg Win"
            value={formatINR(avgWin)}
            color="text-positive"
          />
          <SummaryCard
            label="Avg Loss"
            value={formatINR(Math.abs(avgLoss))}
            color="text-negative"
          />
          <SummaryCard
            label="Profit Factor"
            value={profitFactor.toFixed(2)}
            color={profitFactor >= 1 ? 'text-positive' : 'text-negative'}
          />
          <SummaryCard
            label="Net P&L"
            value={formatINR(totalPnl, true)}
            color={getPnlColor(totalPnl)}
          />
        </div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {timeLoading ? (
          <ChartSkeleton />
        ) : (
          <WinRateChart
            data={timeData}
            title="Win Rate by Time of Day"
            subtitle="Performance across market hours"
          />
        )}
        {instrumentLoading ? (
          <ChartSkeleton />
        ) : (
          <InstrumentBreakdown data={instrumentData} />
        )}
      </div>

      {/* Insights Grid */}
      {insights.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-slate-200 mb-4">Key Insights</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {insights.map((insight, index) => (
              <InsightCard key={insight.id || index} insight={insight} />
            ))}
          </div>
        </div>
      )}

      {/* Hold Time Analysis */}
      {holdTimeAnalysis && (
        <Card>
          <CardHeader
            title="Hold Time Analysis"
            subtitle="How long you hold winning vs losing trades"
          />
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
            <HoldTimeStat
              label="Avg Winner Hold"
              value={holdTimeAnalysis.avg_winner_hold || holdTimeAnalysis.avgWinnerHold || '-'}
              color="text-positive"
            />
            <HoldTimeStat
              label="Avg Loser Hold"
              value={holdTimeAnalysis.avg_loser_hold || holdTimeAnalysis.avgLoserHold || '-'}
              color="text-negative"
            />
            <HoldTimeStat
              label="Optimal Hold"
              value={holdTimeAnalysis.optimal_hold || holdTimeAnalysis.optimalHold || '-'}
              color="text-accent"
            />
            <HoldTimeStat
              label="Hold Efficiency"
              value={
                holdTimeAnalysis.efficiency !== undefined
                  ? `${(holdTimeAnalysis.efficiency * 100).toFixed(0)}%`
                  : holdTimeAnalysis.holdEfficiency !== undefined
                    ? `${(holdTimeAnalysis.holdEfficiency * 100).toFixed(0)}%`
                    : '-'
              }
              color="text-slate-200"
            />
          </div>
          {holdTimeAnalysis.insight && (
            <div className="mt-4 p-3 bg-accent/5 border border-accent/20 rounded-lg">
              <p className="text-sm text-accent/90">{holdTimeAnalysis.insight}</p>
            </div>
          )}
        </Card>
      )}

      {/* Coach Chat */}
      <div>
        <h2 className="text-lg font-semibold text-slate-200 mb-4">Ask the Coach</h2>
        <CoachChat />
      </div>
    </div>
  )
}

function SummaryCard({ label, value, color }) {
  return (
    <div className="bg-navy-800 border border-navy-600 rounded-xl p-4">
      <div className="text-xs text-slate-500 uppercase tracking-wide">{label}</div>
      <div className={`font-mono text-xl font-semibold mt-1 ${color}`}>{value}</div>
    </div>
  )
}

function HoldTimeStat({ label, value, color }) {
  return (
    <div className="bg-navy-700/50 rounded-lg p-3">
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`font-mono text-lg font-semibold mt-1 ${color}`}>{value}</div>
    </div>
  )
}
