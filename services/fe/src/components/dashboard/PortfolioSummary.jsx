import { memo } from 'react'
import { formatINR, formatLakhsCrores, getPnlColor } from '../../utils/formatters'
import { StatCard } from '../common/Card'

function PortfolioSummary({ balance }) {
  if (!balance) return null

  const pnlColor = getPnlColor(balance.total_pnl)

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        label="Net P&L Today"
        value={<span className={pnlColor}>{formatINR(balance.total_pnl, true)}</span>}
        subValue={`${((balance.total_pnl / balance.initial_cash) * 100).toFixed(2)}% of capital`}
        trend={balance.total_pnl >= 0 ? 'up' : 'down'}
        icon={
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        }
      />
      <StatCard
        label="Margin Deployed"
        value={formatLakhsCrores(balance.invested_value)}
        subValue={`${Math.round((balance.invested_value / balance.initial_cash) * 100)}% utilization`}
        icon={
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="2" y="7" width="20" height="14" rx="2" />
            <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
          </svg>
        }
      />
      <StatCard
        label="Available Margin"
        value={formatLakhsCrores(balance.cash)}
        subValue={`of ${formatLakhsCrores(balance.initial_cash)} total`}
        icon={
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
            <path d="M9 12l2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        }
      />
      <StatCard
        label="Total Value"
        value={formatLakhsCrores(balance.total_value)}
        subValue={`${((balance.total_value / balance.initial_cash - 1) * 100).toFixed(2)}% return`}
        icon={
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 3v18h18" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M7 12l4-4 4 4 6-6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        }
      />
    </div>
  )
}

// Memoize to only re-render when balance changes
export default memo(PortfolioSummary)
