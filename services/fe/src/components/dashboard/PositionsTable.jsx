import { useState } from 'react'
import { useApi } from '../../hooks/useApi'
import { getPositions, exitPosition } from '../../api/positions'
import { formatINR, formatPercent, getPnlColor } from '../../utils/formatters'
import Card, { CardHeader } from '../common/Card'
import { TableSkeleton } from '../common/Skeleton'
import ErrorMessage from '../common/ErrorMessage'

export default function PositionsTable() {
  const { data: positions, loading, error, refetch } = useApi(() => getPositions(), [])
  const [exitingPosition, setExitingPosition] = useState(null)
  const [showExitModal, setShowExitModal] = useState(false)
  const [exitSuccess, setExitSuccess] = useState(null)

  if (loading) return <TableSkeleton />
  if (error) return <ErrorMessage error={error} onRetry={refetch} />

  const positionList = positions || []

  const handleExitClick = (position) => {
    setExitingPosition(position)
    setShowExitModal(true)
  }

  const handleConfirmExit = async () => {
    if (!exitingPosition) return
    try {
      await exitPosition(exitingPosition.id)
      setShowExitModal(false)
      setExitSuccess({
        symbol: exitingPosition.symbol,
        pnl: exitingPosition.unrealized_pnl,
      })
      setTimeout(() => setExitSuccess(null), 3000)
      setExitingPosition(null)
      refetch()
    } catch (err) {
      console.error('Exit failed:', err)
    }
  }

  const handleCancelExit = () => {
    setShowExitModal(false)
    setExitingPosition(null)
  }

  return (
    <Card>
      <CardHeader
        title="Open Positions"
        subtitle={`${positionList.length} active`}
        action={
          positionList.length > 0 && (
            <span className="text-xs text-slate-500 font-mono">
              Net: <span className={getPnlColor(positionList.reduce((sum, p) => sum + p.unrealized_pnl, 0))}>
                {formatINR(positionList.reduce((sum, p) => sum + p.unrealized_pnl, 0), true)}
              </span>
            </span>
          )
        }
      />

      {/* Success toast */}
      {exitSuccess && (
        <div className="mb-4 px-3 py-2 bg-positive/10 border border-positive/30 rounded-lg flex items-center gap-2">
          <svg className="w-4 h-4 text-positive flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          <span className="text-xs text-positive">
            Exited {exitSuccess.symbol} at {formatINR(exitSuccess.pnl, true)}
          </span>
        </div>
      )}

      {positionList.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-12 h-12 rounded-full bg-navy-700 flex items-center justify-center mx-auto mb-3">
            <svg className="w-6 h-6 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M20 12H4" />
            </svg>
          </div>
          <p className="text-sm text-slate-500">No open positions</p>
          <p className="text-xs text-slate-600 mt-1">Positions will appear here when trades are active</p>
        </div>
      ) : (
        <div className="overflow-x-auto -mx-5">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-navy-700">
                <th className="text-left text-xs text-slate-500 font-medium uppercase tracking-wide px-5 pb-3">Symbol</th>
                <th className="text-left text-xs text-slate-500 font-medium uppercase tracking-wide px-3 pb-3">Side</th>
                <th className="text-right text-xs text-slate-500 font-medium uppercase tracking-wide px-3 pb-3">Qty</th>
                <th className="text-right text-xs text-slate-500 font-medium uppercase tracking-wide px-3 pb-3">Avg Price</th>
                <th className="text-right text-xs text-slate-500 font-medium uppercase tracking-wide px-3 pb-3">LTP</th>
                <th className="text-right text-xs text-slate-500 font-medium uppercase tracking-wide px-3 pb-3">P&L</th>
                <th className="text-right text-xs text-slate-500 font-medium uppercase tracking-wide px-5 pb-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {positionList.map((position) => {
                const pnlColor = getPnlColor(position.unrealized_pnl)
                const sideColor = position.side === 'BUY' ? 'text-positive' : 'text-negative'
                const sideBg = position.side === 'BUY' ? 'bg-positive/10' : 'bg-negative/10'

                return (
                  <tr key={position.id} className="border-b border-navy-700/50 hover:bg-navy-700/30 transition-colors">
                    <td className="px-5 py-3">
                      <div className="font-medium text-slate-200">{position.symbol}</div>
                      {position.instrument && (
                        <div className="text-xs text-slate-500 mt-0.5">{position.instrument}</div>
                      )}
                    </td>
                    <td className="px-3 py-3">
                      <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${sideColor} ${sideBg}`}>
                        {position.side}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-right font-mono text-slate-300">
                      {position.quantity}
                    </td>
                    <td className="px-3 py-3 text-right font-mono text-slate-300">
                      {formatINR(position.avg_price)}
                    </td>
                    <td className="px-3 py-3 text-right font-mono text-slate-300">
                      {formatINR(position.current_price)}
                    </td>
                    <td className="px-3 py-3 text-right">
                      <div className={`font-mono font-medium ${pnlColor}`}>
                        {formatINR(position.unrealized_pnl, true)}
                      </div>
                      <div className={`text-xs font-mono ${pnlColor}`}>
                        {formatPercent(position.pnl_pct, true)}
                      </div>
                    </td>
                    <td className="px-5 py-3 text-right">
                      <button
                        onClick={() => handleExitClick(position)}
                        className="px-3 py-1.5 text-xs font-medium text-negative bg-negative/10 hover:bg-negative/20 border border-negative/30 rounded-lg transition-colors"
                      >
                        Exit
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Exit confirmation modal */}
      {showExitModal && exitingPosition && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-navy-800 border border-navy-600 rounded-xl p-6 max-w-sm w-full mx-4 shadow-2xl">
            <h3 className="text-lg font-semibold text-slate-200 mb-2">Confirm Exit</h3>
            <p className="text-sm text-slate-400 mb-4">
              Exit <span className="text-slate-200 font-medium">{exitingPosition.symbol}</span>{' '}
              <span className={exitingPosition.side === 'BUY' ? 'text-positive' : 'text-negative'}>
                {exitingPosition.side}
              </span>{' '}
              {exitingPosition.quantity} qty at market?
            </p>

            <div className="bg-navy-700/50 rounded-lg p-3 mb-5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500">Unrealized P&L</span>
                <span className={`font-mono font-medium ${getPnlColor(exitingPosition.unrealized_pnl)}`}>
                  {formatINR(exitingPosition.unrealized_pnl, true)}
                </span>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleCancelExit}
                className="flex-1 px-4 py-2.5 text-sm font-medium text-slate-400 bg-navy-700 hover:bg-navy-600 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmExit}
                className="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-negative hover:bg-negative/80 rounded-lg transition-colors"
              >
                Exit Position
              </button>
            </div>
          </div>
        </div>
      )}
    </Card>
  )
}
