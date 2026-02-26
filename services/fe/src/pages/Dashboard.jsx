import { useApi } from '../hooks/useApi'
import { getBalance, getHistory } from '../api/portfolio'
import { getWeeklyPnl } from '../api/trades'
import PortfolioSummary from '../components/dashboard/PortfolioSummary'
import PositionsTable from '../components/dashboard/PositionsTable'
import PLChart from '../components/dashboard/PLChart'
import WeeklyPLChart from '../components/dashboard/WeeklyPLChart'
import { formatINR, formatLakhsCrores } from '../utils/formatters'
import { CardSkeleton, ChartSkeleton } from '../components/common/Skeleton'
import ErrorMessage from '../components/common/ErrorMessage'

export default function Dashboard() {
  const { data: balance, loading: balanceLoading, error: balanceError, refetch: refetchBalance } = useApi(() => getBalance(), [])
  const { data: historyData } = useApi(() => getHistory('1d'), [])
  const { data: weeklyData } = useApi(() => getWeeklyPnl(), [])

  const dailyLossLimit = 25000
  const pnl = balance?.total_pnl || 0
  const bufferRemaining = dailyLossLimit - Math.abs(Math.min(0, pnl))
  const bufferPercent = (bufferRemaining / dailyLossLimit) * 100

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">Portfolio overview and performance metrics</p>
        </div>
        {/* Daily loss limit indicator */}
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-xs text-slate-500">Daily Loss Limit</div>
            <div className="font-mono text-sm text-slate-300">{formatINR(dailyLossLimit)}</div>
          </div>
          <div className="w-32 h-2 bg-navy-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                bufferPercent > 50 ? 'bg-positive' : bufferPercent > 25 ? 'bg-warning' : 'bg-negative'
              }`}
              style={{ width: `${Math.max(0, bufferPercent)}%` }}
            />
          </div>
          <div className="text-xs text-slate-500">{formatINR(bufferRemaining)} buffer</div>
        </div>
      </div>

      {/* Portfolio Summary Cards */}
      {balanceLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <CardSkeleton /><CardSkeleton /><CardSkeleton /><CardSkeleton />
        </div>
      ) : balanceError ? (
        <ErrorMessage error={balanceError} onRetry={refetchBalance} />
      ) : (
        <PortfolioSummary balance={balance} />
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PLChart data={historyData} />
        <WeeklyPLChart data={weeklyData} />
      </div>

      {/* Positions Table */}
      <PositionsTable />

      {/* Quick Actions */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <QuickAction
          icon={<svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" strokeLinecap="round" /></svg>}
          label="Market Hours"
          value="09:15 - 15:30"
          sublabel="NSE/BSE"
        />
        <QuickAction
          icon={<svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" strokeLinecap="round" strokeLinejoin="round" /></svg>}
          label="Capital"
          value={formatLakhsCrores(balance?.initial_cash || 0)}
          sublabel="Total deployed"
        />
        <QuickAction
          icon={<svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2" strokeLinecap="round" strokeLinejoin="round" /></svg>}
          label="Max Drawdown"
          value={formatINR(0)}
          sublabel="Today's low"
          highlight
        />
        <QuickAction
          icon={<svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>}
          label="Risk Level"
          value="Moderate"
          sublabel="Based on positions"
        />
      </div>
    </div>
  )
}

function QuickAction({ icon, label, value, sublabel, highlight }) {
  return (
    <div className={`bg-navy-800 border rounded-xl p-4 ${highlight ? 'border-warning/30' : 'border-navy-600'}`}>
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
          highlight ? 'bg-warning/10 text-warning' : 'bg-navy-700 text-slate-400'
        }`}>
          {icon}
        </div>
        <div>
          <div className="text-xs text-slate-500">{label}</div>
          <div className={`font-mono text-sm font-medium ${highlight ? 'text-warning' : 'text-slate-200'}`}>{value}</div>
          <div className="text-xs text-slate-600">{sublabel}</div>
        </div>
      </div>
    </div>
  )
}
