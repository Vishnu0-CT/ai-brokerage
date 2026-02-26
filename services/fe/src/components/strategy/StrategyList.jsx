import Card from '../common/Card'
import { formatINR } from '../../utils/formatters'

export default function StrategyList({ strategies, onSelect, onToggle, onDelete, onEdit }) {
  if (!strategies || strategies.length === 0) {
    return null
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-200">My Strategies</h2>
        <div className="text-sm text-slate-400">
          {strategies.filter(s => s.status === 'active').length} active / {strategies.length} total
        </div>
      </div>

      <div className="grid gap-4">
        {strategies.map((strategy) => (
          <StrategyCard
            key={strategy.id}
            strategy={strategy}
            onSelect={() => onSelect(strategy)}
            onToggle={() => onToggle(strategy.id)}
            onDelete={() => onDelete(strategy.id)}
            onEdit={() => onEdit(strategy)}
          />
        ))}
      </div>
    </div>
  )
}

function StrategyCard({ strategy, onSelect, onToggle, onDelete, onEdit }) {
  const isActive = strategy.status === 'active'
  const stats = strategy.paper_trading_stats || strategy.paperTradingStats || {}
  const pnlColor = (stats.totalPnl || stats.total_pnl || 0) >= 0 ? 'text-positive' : 'text-negative'

  return (
    <Card className="hover:border-navy-500 transition-colors cursor-pointer" onClick={onSelect}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-xl">
              {strategy.action?.type === 'BUY' ? '📈' : '📉'}
            </span>
            <h3 className="text-lg font-semibold text-slate-100">{strategy.name}</h3>
            <StatusBadge status={strategy.status} />
          </div>
          <p className="text-sm text-slate-400 mb-4">{strategy.description}</p>

          <div className="flex items-center gap-6 text-sm">
            <div>
              <span className="text-slate-500">Trades:</span>
              <span className="ml-2 text-slate-300 font-medium">{stats.totalTrades || stats.total_trades || 0}</span>
            </div>
            <div>
              <span className="text-slate-500">Win Rate:</span>
              <span className="ml-2 text-slate-300 font-medium">{stats.winRate || stats.win_rate || 0}%</span>
            </div>
            <div>
              <span className="text-slate-500">P&L:</span>
              <span className={`ml-2 font-semibold ${pnlColor}`}>
                {formatINR(stats.totalPnl || stats.total_pnl || 0, true)}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={onToggle}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
              isActive
                ? 'bg-positive/10 text-positive hover:bg-positive/20'
                : 'bg-navy-600 text-slate-400 hover:bg-navy-500'
            }`}
          >
            {isActive ? 'Pause' : 'Activate'}
          </button>
          <button
            onClick={onEdit}
            className="p-1.5 text-slate-500 hover:text-accent transition-colors"
            title="Edit strategy"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            onClick={onDelete}
            className="p-1.5 text-slate-500 hover:text-negative transition-colors"
            title="Delete strategy"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-navy-600 flex items-center gap-4 text-xs text-slate-500">
        <span>
          {strategy.action?.instrument} {strategy.action?.optionType}
        </span>
        <span>•</span>
        <span>
          {strategy.entry_conditions?.length || strategy.entryConditions?.length || 0} entry condition{(strategy.entry_conditions?.length || strategy.entryConditions?.length) !== 1 ? 's' : ''}
        </span>
        <span>•</span>
        <span>
          Created {new Date(strategy.created_at || strategy.createdAt).toLocaleDateString('en-IN')}
        </span>
      </div>
    </Card>
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
