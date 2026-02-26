import Card from '../common/Card'
import ConditionBadge from './ConditionBadge'

export default function ParsedStrategy({ strategy, onConfirm, onEdit, confirmLabel = 'Confirm & Save Strategy' }) {
  if (!strategy) return null

  // Handle both camelCase and snake_case from API
  const entryConditions = strategy.entryConditions || strategy.entry_conditions || []
  const exitConditions = strategy.exitConditions || strategy.exit_conditions || []
  const positionSize = strategy.positionSize || strategy.position_size || {}
  const stopLoss = strategy.stopLoss || strategy.stop_loss
  const target = strategy.target

  return (
    <Card className="border-2 border-accent/30">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-slate-100">{strategy.name}</h3>
        <p className="text-sm text-slate-400 mt-1">{strategy.description}</p>
      </div>

      {/* Entry Conditions */}
      <div className="mb-6">
        <div className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-3">
          Entry Conditions
        </div>
        <div className="flex flex-wrap gap-2">
          {entryConditions.length > 0 ? (
            entryConditions.map((condition, idx) => (
              <ConditionBadge key={idx} condition={condition} type="entry" />
            ))
          ) : (
            <span className="text-sm text-slate-500 italic">No specific conditions parsed</span>
          )}
        </div>
      </div>

      {/* Action */}
      <div className="mb-6">
        <div className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-3">
          Action
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {strategy.action ? (
            <>
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
              <span className="text-xs text-slate-500 bg-navy-700 px-2 py-1 rounded">
                {strategy.action?.orderType}
              </span>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <span className="px-3 py-1.5 rounded-lg text-sm font-semibold bg-negative/20 text-negative">
                SELL
              </span>
              <span className="text-slate-200 font-medium">
                {positionSize.value || 1} lot{(positionSize.value || 1) > 1 ? 's' : ''}
              </span>
              <span className="text-sm text-slate-400 italic">
                (Action derived from strategy type)
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Exit Conditions */}
      <div className="mb-6">
        <div className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-3">
          Exit Conditions
        </div>
        <div className="flex flex-wrap gap-2">
          {exitConditions.length > 0 ? (
            exitConditions.map((condition, idx) => (
              <ConditionBadge key={idx} condition={condition} type="exit" />
            ))
          ) : (
            <span className="text-sm text-slate-500 italic">No exit conditions specified</span>
          )}
          {stopLoss && (
            <ConditionBadge condition={{ type: 'stoploss', value: stopLoss.value, unit: stopLoss.unit }} type="exit" />
          )}
          {target && (
            <ConditionBadge condition={{ type: 'target', value: target.value, unit: target.unit }} type="exit" />
          )}
        </div>
      </div>

      {/* Time Filter & Risk Params */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {strategy.timeFilter && (
          <div className="bg-navy-700/50 rounded-lg p-3">
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">
              Trading Hours
            </div>
            <div className="text-sm text-slate-300">
              {strategy.timeFilter.startTime} - {strategy.timeFilter.endTime}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              {strategy.timeFilter.tradingDays?.slice(0, 3).join(', ')}...
            </div>
          </div>
        )}
        {strategy.riskParams && (
          <div className="bg-navy-700/50 rounded-lg p-3">
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">
              Risk Parameters
            </div>
            <div className="text-sm text-slate-300">
              Max {strategy.riskParams.maxTradesPerDay} trades/day
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Daily loss limit: \u20b9{strategy.riskParams.maxDailyLoss?.toLocaleString('en-IN')}
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t border-navy-600">
        <button
          onClick={onEdit}
          className="px-4 py-2 text-slate-400 hover:text-slate-200 transition-colors"
        >
          Edit Input
        </button>
        <button
          onClick={onConfirm}
          className="flex items-center gap-2 px-6 py-2.5 bg-accent hover:bg-accent-light text-navy-900 font-medium rounded-lg transition-colors"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          {confirmLabel}
        </button>
      </div>
    </Card>
  )
}
