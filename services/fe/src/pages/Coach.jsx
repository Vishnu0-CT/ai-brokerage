import { useMemo, useEffect, useState } from 'react'
import { useApi } from '../hooks/useApi'
import { useWatchlistPriceStream } from '../hooks/useWatchlistPriceStream'
import { getCoaching, getWinRateByTime, getInstrumentStats } from '../api/analytics'
import { getBalance, getHoldings } from '../api/portfolio'
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
  const { data: timeDataRaw, loading: timeLoading, refetch: refetchTimeData } = useApi(() => getWinRateByTime(), [])
  const { data: instrumentDataRaw, loading: instrumentLoading, refetch: refetchInstrumentData } = useApi(() => getInstrumentStats(), [])
  const { data: balance } = useApi(() => getBalance(), [])
  const { data: positions } = useApi(() => getHoldings(), [])
  const { priceUpdates } = useWatchlistPriceStream(true)

  const [lastRefresh, setLastRefresh] = useState(Date.now())
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [, forceUpdate] = useState(0)

  // Manual refresh function
  const handleManualRefresh = async () => {
    setIsRefreshing(true)
    await Promise.all([
      refetchCoaching(),
      refetchTimeData(),
      refetchInstrumentData()
    ])
    setLastRefresh(Date.now())
    setIsRefreshing(false)
  }

  // Update the "Updated X seconds ago" display every second
  useEffect(() => {
    const timer = setInterval(() => {
      forceUpdate(n => n + 1)
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  // Periodically refresh coaching data to pick up completed trades (every 30 seconds)
  useEffect(() => {
    const interval = setInterval(async () => {
      await Promise.all([
        refetchCoaching(),
        refetchTimeData(),
        refetchInstrumentData()
      ])
      setLastRefresh(Date.now())
    }, 30000) // 30 seconds

    return () => clearInterval(interval)
  }, [refetchCoaching, refetchTimeData, refetchInstrumentData])

  // Calculate real-time P&L including unrealized gains/losses (MUST BE BEFORE timeData)
  const realTimeTotalPnl = useMemo(() => {
    const historicalPnl = coaching?.summary?.total_pnl || coaching?.summary?.totalPnl || 0

    if (!balance || !positions || Object.keys(priceUpdates).length === 0) {
      // Use current balance total_pnl if available, otherwise fall back to coaching summary
      return balance?.total_pnl ?? historicalPnl
    }

    // Calculate current unrealized P&L with real-time prices
    let totalUnrealizedPnl = 0
    positions.forEach(position => {
      const baseSymbol = position.symbol.split(' ')[0]
      const priceUpdate = priceUpdates[baseSymbol]

      if (priceUpdate && priceUpdate.price && position.symbol === baseSymbol) {
        const currentPrice = priceUpdate.price
        const isLong = position.side === 'BUY' || position.side === 'long'
        const pnl = (currentPrice - position.avg_price) * position.quantity * (isLong ? 1 : -1)
        totalUnrealizedPnl += pnl
      } else {
        totalUnrealizedPnl += position.unrealized_pnl || 0
      }
    })

    const realizedPnl = balance.realized_pnl || 0
    return realizedPnl + totalUnrealizedPnl
  }, [coaching, balance, positions, priceUpdates])

  // Transform timeData and add current session info
  const { timeData, currentTimeSlot } = useMemo(() => {
    const baseData = timeDataRaw ? Object.entries(timeDataRaw).map(([key, value]) => ({
      label: key.charAt(0).toUpperCase() + key.slice(1),
      winRate: value.win_rate ?? value.winRate ?? 0,
      trades: value.trades ?? 0,
      pnl: value.pnl ?? 0,
      historicalPnl: value.pnl ?? 0,
    })) : []

    // Determine current time slot
    const now = new Date()
    const hour = now.getHours()
    let currentSlot = null

    if (hour >= 9 && hour < 12) currentSlot = 'Morning'
    else if (hour >= 12 && hour < 15) currentSlot = 'Afternoon'
    else if (hour >= 15 && hour < 18) currentSlot = 'Evening'

    // Add current unrealized P&L to the current time slot
    if (currentSlot && realTimeTotalPnl !== undefined) {
      const slotIndex = baseData.findIndex(d => d.label === currentSlot)
      if (slotIndex !== -1) {
        const currentSessionPnl = realTimeTotalPnl - (balance?.realized_pnl || 0)
        baseData[slotIndex] = {
          ...baseData[slotIndex],
          pnl: baseData[slotIndex].historicalPnl + currentSessionPnl,
          currentSessionPnl,
          isCurrentSlot: true,
        }
      }
    }

    return { timeData: baseData, currentTimeSlot: currentSlot }
  }, [timeDataRaw, realTimeTotalPnl, balance])

  // Transform instrumentData and add real-time unrealized P&L
  const instrumentData = useMemo(() => {
    const baseData = instrumentDataRaw ? Object.entries(instrumentDataRaw).map(([key, value]) => ({
      instrument: key,
      avgPnl: value.avg_pnl ?? value.avgPnl ?? 0,
      winRate: value.win_rate ?? value.winRate ?? 0,
      trades: value.trades ?? 0,
      pnl: value.pnl ?? 0,
      realizedPnl: value.pnl ?? 0, // Store historical realized P&L
    })) : []

    // Add real-time unrealized P&L from open positions
    if (!positions || Object.keys(priceUpdates).length === 0) {
      return baseData
    }

    // Calculate unrealized P&L by instrument
    const unrealizedByInstrument = {}
    positions.forEach(position => {
      const baseSymbol = position.symbol.split(' ')[0]
      const priceUpdate = priceUpdates[baseSymbol]

      let unrealizedPnl = position.unrealized_pnl || 0

      // Use real-time price if available
      if (priceUpdate && priceUpdate.price && position.symbol === baseSymbol) {
        const currentPrice = priceUpdate.price
        const isLong = position.side === 'BUY' || position.side === 'long'
        unrealizedPnl = (currentPrice - position.avg_price) * position.quantity * (isLong ? 1 : -1)
      }

      if (!unrealizedByInstrument[baseSymbol]) {
        unrealizedByInstrument[baseSymbol] = 0
      }
      unrealizedByInstrument[baseSymbol] += unrealizedPnl
    })

    // Merge with historical data
    const instrumentMap = new Map(baseData.map(item => [item.instrument, item]))

    // Add unrealized P&L to existing instruments
    Object.entries(unrealizedByInstrument).forEach(([instrument, unrealizedPnl]) => {
      if (instrumentMap.has(instrument)) {
        const item = instrumentMap.get(instrument)
        item.pnl = item.realizedPnl + unrealizedPnl
        item.unrealizedPnl = unrealizedPnl
        item.hasOpenPositions = true
      } else {
        // Add new instrument with only unrealized P&L
        instrumentMap.set(instrument, {
          instrument,
          avgPnl: unrealizedPnl, // Current unrealized is the "average" for open positions
          winRate: 0,
          trades: 0,
          pnl: unrealizedPnl,
          realizedPnl: 0,
          unrealizedPnl,
          hasOpenPositions: true,
        })
      }
    })

    return Array.from(instrumentMap.values())
  }, [instrumentDataRaw, positions, priceUpdates])

  const summary = coaching?.summary || {}
  const insights = coaching?.insights || []
  const holdTimeAnalysis = coaching?.hold_time_analysis || coaching?.holdTimeAnalysis || null

  const winRate = summary.win_rate || summary.winRate || 0
  const totalTrades = summary.total_trades || summary.totalTrades || 0
  const avgWin = summary.avg_win || summary.avgWin || 0
  const avgLoss = summary.avg_loss || summary.avgLoss || 0
  const profitFactor = summary.profit_factor || summary.profitFactor || 0

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">Clear Coach</h1>
          <p className="text-sm text-slate-500 mt-1">AI-powered analysis of your trading patterns</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-navy-700/50 rounded-full">
            <div className="w-2 h-2 rounded-full bg-accent pulse-live" />
            <span className="text-xs text-slate-400">
              Updated {Math.floor((Date.now() - lastRefresh) / 1000)}s ago
            </span>
          </div>
          <button
            onClick={handleManualRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-3 py-1.5 bg-navy-700 hover:bg-navy-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-xs text-slate-300 transition-colors"
          >
            <svg
              className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`}
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Refresh
          </button>
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
            value={formatINR(realTimeTotalPnl, true)}
            color={getPnlColor(realTimeTotalPnl)}
            live={true}
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

function SummaryCard({ label, value, color, live }) {
  return (
    <div className="bg-navy-800 border border-navy-600 rounded-xl p-4 relative">
      <div className="flex items-center justify-between">
        <div className="text-xs text-slate-500 uppercase tracking-wide">{label}</div>
        {live && (
          <div className="flex items-center gap-1">
            <div className="w-1.5 h-1.5 rounded-full bg-positive pulse-live" />
          </div>
        )}
      </div>
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
