import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import { getAlerts, getRiskMetrics, dismissAlert as dismissAlertApi } from '../api/alerts'
import { getTradingSignal } from '../api/analytics'
import { getHistory } from '../api/portfolio'
import RiskGauge from '../components/risk/RiskGauge'
import AlertCard from '../components/risk/AlertCard'
import DrawdownTracker from '../components/risk/DrawdownTracker'
import { CardSkeleton, ChartSkeleton } from '../components/common/Skeleton'
import ErrorMessage from '../components/common/ErrorMessage'

export default function RiskMonitor() {
  const [alertFilter, setAlertFilter] = useState('all')

  const { data: alerts, loading: alertsLoading, error: alertsError, refetch: refetchAlerts } = useApi(() => getAlerts(), [])
  const { data: riskMetrics, loading: metricsLoading, error: metricsError, refetch: refetchMetrics } = useApi(() => getRiskMetrics(), [])
  const { data: signal, loading: signalLoading } = useApi(() => getTradingSignal(), [])
  const { data: historyData } = useApi(() => getHistory('1d'), [])

  const handleDismiss = async (id) => {
    try {
      await dismissAlertApi(id)
      refetchAlerts()
    } catch {
      // Alert may already be dismissed
    }
  }

  const filteredAlerts = alerts?.filter((alert) => {
    if (alertFilter === 'all') return true
    return alert.severity === alertFilter
  }) || []

  const activeAlertCount = alerts?.filter(a => !a.dismissed)?.length || 0
  const criticalCount = alerts?.filter(a => a.severity === 'critical')?.length || 0

  // Extract risk metrics safely
  const drawdownPct = riskMetrics?.drawdown_percent || riskMetrics?.drawdown?.percent || 0
  const drawdownValue = riskMetrics?.drawdown_value || riskMetrics?.drawdown?.value || 0
  const dailyLossLimit = riskMetrics?.daily_loss_limit || 25000
  const tradeVelocity = riskMetrics?.trade_velocity || riskMetrics?.trades_today || 0
  const maxTradesPerDay = riskMetrics?.max_trades_per_day || 20
  const concentrationPct = riskMetrics?.concentration_percent || riskMetrics?.concentration?.percent || 0
  const concentrationMax = riskMetrics?.concentration_max || 100
  const marginUsed = riskMetrics?.margin_used || riskMetrics?.margin_utilization || 0
  const marginMax = riskMetrics?.margin_total || 100

  // Signal data
  const signalValue = signal?.signal || signal?.value || 'NEUTRAL'
  const signalColor = signalValue === 'GO' || signalValue === 'BULLISH'
    ? 'text-positive'
    : signalValue === 'STOP' || signalValue === 'BEARISH'
      ? 'text-negative'
      : 'text-warning'

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">Risk Monitor</h1>
          <p className="text-sm text-slate-500 mt-1">Real-time risk metrics and behavioural alerts</p>
        </div>
        <div className="flex items-center gap-4">
          {/* Trading signal */}
          <div className="flex items-center gap-3 px-4 py-2 bg-navy-800 border border-navy-600 rounded-xl">
            <div className="text-xs text-slate-500">Trading Signal</div>
            {signalLoading ? (
              <div className="h-5 w-16 bg-navy-700 rounded animate-pulse" />
            ) : (
              <div className={`font-mono text-sm font-bold ${signalColor}`}>
                {signalValue}
              </div>
            )}
          </div>
          {/* Active alerts badge */}
          {activeAlertCount > 0 && (
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
              criticalCount > 0 ? 'bg-negative/20 text-negative' : 'bg-warning/20 text-warning'
            }`}>
              <div className="w-2 h-2 rounded-full bg-current pulse-live" />
              <span className="text-xs font-medium">{activeAlertCount} Active Alert{activeAlertCount !== 1 ? 's' : ''}</span>
            </div>
          )}
        </div>
      </div>

      {/* Risk Gauges */}
      {metricsLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <CardSkeleton /><CardSkeleton /><CardSkeleton /><CardSkeleton />
        </div>
      ) : metricsError ? (
        <ErrorMessage error={metricsError} onRetry={refetchMetrics} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <RiskGauge
            label="Daily Drawdown"
            value={Math.abs(drawdownValue)}
            max={dailyLossLimit}
            unit="INR"
            status={
              Math.abs(drawdownValue) > dailyLossLimit * 0.9 ? 'critical' :
              Math.abs(drawdownValue) > dailyLossLimit * 0.7 ? 'warning' :
              Math.abs(drawdownValue) > dailyLossLimit * 0.5 ? 'elevated' : 'normal'
            }
            description="P&L drawdown vs daily loss limit"
          />
          <RiskGauge
            label="Trade Velocity"
            value={tradeVelocity}
            max={maxTradesPerDay}
            unit="trades"
            status={
              tradeVelocity > maxTradesPerDay * 0.9 ? 'critical' :
              tradeVelocity > maxTradesPerDay * 0.7 ? 'warning' :
              tradeVelocity > maxTradesPerDay * 0.5 ? 'elevated' : 'normal'
            }
            description="Trades executed today"
          />
          <RiskGauge
            label="Concentration"
            value={concentrationPct}
            max={concentrationMax}
            unit="%"
            status={
              concentrationPct > 80 ? 'critical' :
              concentrationPct > 60 ? 'warning' :
              concentrationPct > 40 ? 'elevated' : 'normal'
            }
            description="Largest single-instrument exposure"
          />
          <RiskGauge
            label="Margin Utilization"
            value={marginUsed}
            max={marginMax}
            unit="%"
            status={
              marginUsed > 90 ? 'critical' :
              marginUsed > 70 ? 'warning' :
              marginUsed > 50 ? 'elevated' : 'normal'
            }
            description="Deployed margin vs available"
          />
        </div>
      )}

      {/* Drawdown Tracker + Behaviour */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <DrawdownTracker historyData={historyData} dailyLossLimit={dailyLossLimit} />
        </div>
        <div className="space-y-4">
          <div className="bg-navy-800 border border-navy-600 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-slate-200 mb-4">Behaviour Monitor</h3>
            <div className="space-y-3">
              <BehaviourItem
                label="Revenge Trading"
                score={riskMetrics?.revenge_score || 0}
                maxScore={10}
                description="Emotional trading after losses"
              />
              <BehaviourItem
                label="Overtrading"
                score={riskMetrics?.overtrading_score || 0}
                maxScore={10}
                description="Excessive trade frequency"
              />
              <BehaviourItem
                label="Position Sizing"
                score={riskMetrics?.sizing_score || 0}
                maxScore={10}
                description="Size consistency"
              />
              <BehaviourItem
                label="Discipline"
                score={riskMetrics?.discipline_score || 0}
                maxScore={10}
                description="Adherence to strategy"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Alerts Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-200">Risk Alerts</h2>
          <div className="flex items-center gap-2">
            {['all', 'critical', 'high', 'medium', 'low'].map((filter) => (
              <button
                key={filter}
                onClick={() => setAlertFilter(filter)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  alertFilter === filter
                    ? 'bg-accent text-navy-900'
                    : 'bg-navy-700 text-slate-400 hover:bg-navy-600'
                }`}
              >
                {filter.charAt(0).toUpperCase() + filter.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {alertsLoading ? (
          <div className="space-y-4">
            <CardSkeleton /><CardSkeleton />
          </div>
        ) : alertsError ? (
          <ErrorMessage error={alertsError} onRetry={refetchAlerts} />
        ) : filteredAlerts.length === 0 ? (
          <div className="bg-navy-800 border border-navy-600 rounded-xl p-12 text-center">
            <div className="w-16 h-16 rounded-2xl bg-positive/10 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-positive" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-slate-300 mb-2">All Clear</h3>
            <p className="text-sm text-slate-500">No active risk alerts. Trading within safe parameters.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredAlerts.map((alert) => (
              <AlertCard key={alert.id} alert={alert} onDismiss={handleDismiss} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function BehaviourItem({ label, score, maxScore, description }) {
  const percentage = (score / maxScore) * 100

  const getColor = () => {
    if (percentage > 70) return { bar: 'bg-negative', text: 'text-negative' }
    if (percentage > 40) return { bar: 'bg-warning', text: 'text-warning' }
    return { bar: 'bg-positive', text: 'text-positive' }
  }

  const colors = getColor()

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-sm text-slate-300">{label}</span>
          <p className="text-xs text-slate-600">{description}</p>
        </div>
        <span className={`font-mono text-sm font-semibold ${colors.text}`}>
          {score}/{maxScore}
        </span>
      </div>
      <div className="h-1.5 bg-navy-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${colors.bar}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
