import { useState, useCallback } from 'react'
import { useApi } from '../hooks/useApi'
import {
  listStrategies,
  createStrategy as createStrategyApi,
  updateStrategy,
  deleteStrategy as deleteStrategyApi,
  parseStrategy,
  getTemplates,
} from '../api/strategies'
import ParsedStrategy from '../components/strategy/ParsedStrategy'
import ConditionBadge from '../components/strategy/ConditionBadge'
import { formatINR, timeAgo } from '../utils/formatters'
import { CardSkeleton } from '../components/common/Skeleton'
import ErrorMessage from '../components/common/ErrorMessage'
import Card from '../components/common/Card'

const VIEWS = { LIST: 'list', CREATE: 'create', DETAIL: 'detail' }

export default function StrategyBuilder() {
  const [view, setView] = useState(VIEWS.LIST)
  const [selectedStrategy, setSelectedStrategy] = useState(null)
  const [editingStrategy, setEditingStrategy] = useState(null)
  const [description, setDescription] = useState('')
  const [parsedResult, setParsedResult] = useState(null)
  const [parseLoading, setParseLoading] = useState(false)
  const [parseError, setParseError] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [actionError, setActionError] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const { data: strategies, loading: strategiesLoading, error: strategiesError, refetch: refetchStrategies } = useApi(
    () => listStrategies(),
    [refreshKey]
  )

  const { data: templates } = useApi(() => getTemplates(), [])

  const refetch = useCallback(() => {
    setRefreshKey(k => k + 1)
  }, [])

  const handleParse = async () => {
    if (!description.trim()) return
    setParseLoading(true)
    setParseError(null)
    setParsedResult(null)

    try {
      const result = await parseStrategy(description)
      setParsedResult(result)
    } catch (err) {
      setParseError(err.message || 'Failed to parse strategy')
    } finally {
      setParseLoading(false)
    }
  }

  const handleConfirmStrategy = async () => {
    if (!parsedResult) return
    setActionLoading(true)
    setActionError(null)

    const body = {
      name: parsedResult.name,
      description: parsedResult.description || description,
      entry_conditions: parsedResult.entryConditions,
      exit_conditions: parsedResult.exitConditions,
      action: parsedResult.action,
      time_filter: parsedResult.timeFilter,
      risk_params: parsedResult.riskParams,
      confidence: parsedResult.confidence,
    }

    try {
      if (editingStrategy) {
        await updateStrategy(editingStrategy.id, body)
      } else {
        await createStrategyApi(body)
      }
      refetch()
      setView(VIEWS.LIST)
      setDescription('')
      setParsedResult(null)
      setEditingStrategy(null)
    } catch (err) {
      setActionError(err.message || 'Failed to save strategy')
    } finally {
      setActionLoading(false)
    }
  }

  const handleToggleStrategy = async (strategy) => {
    const newStatus = strategy.status === 'active' ? 'paused' : 'active'
    try {
      await updateStrategy(strategy.id, { status: newStatus })
      refetch()
    } catch {
      // Silently fail — user can retry
    }
  }

  const handleDeleteStrategy = async (strategy) => {
    try {
      await deleteStrategyApi(strategy.id)
      refetch()
      if (selectedStrategy?.id === strategy.id) {
        setSelectedStrategy(null)
        setView(VIEWS.LIST)
      }
    } catch {
      // Silently fail — user can retry
    }
  }

  const handleEdit = (strategy) => {
    setEditingStrategy(strategy)
    setDescription(strategy.description || '')
    setParsedResult({
      name: strategy.name,
      description: strategy.description,
      entryConditions: strategy.entry_conditions || strategy.entryConditions || [],
      exitConditions: strategy.exit_conditions || strategy.exitConditions || [],
      action: strategy.action,
      timeFilter: strategy.time_filter || strategy.timeFilter,
      riskParams: strategy.risk_params || strategy.riskParams,
      confidence: strategy.confidence,
    })
    setView(VIEWS.CREATE)
  }

  const handleViewDetail = (strategy) => {
    setSelectedStrategy(strategy)
    setView(VIEWS.DETAIL)
  }

  const handleStartCreate = (templateDescription) => {
    setEditingStrategy(null)
    setDescription(templateDescription || '')
    setParsedResult(null)
    setParseError(null)
    setView(VIEWS.CREATE)
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">Strategy Builder</h1>
          <p className="text-sm text-slate-500 mt-1">Create and manage automated trading strategies</p>
        </div>
        <div className="flex items-center gap-3">
          {view !== VIEWS.LIST && (
            <button
              onClick={() => { setView(VIEWS.LIST); setEditingStrategy(null); setParsedResult(null) }}
              className="px-4 py-2 text-sm text-slate-400 hover:text-slate-200 bg-navy-700 hover:bg-navy-600 rounded-lg transition-colors"
            >
              Back to List
            </button>
          )}
          {view === VIEWS.LIST && (
            <button
              onClick={() => handleStartCreate('')}
              className="flex items-center gap-2 px-4 py-2 bg-accent hover:bg-accent-light text-navy-900 font-medium text-sm rounded-lg transition-colors"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 5v14M5 12h14" strokeLinecap="round" />
              </svg>
              New Strategy
            </button>
          )}
        </div>
      </div>

      {/* LIST VIEW */}
      {view === VIEWS.LIST && (
        <div className="space-y-6">
          {/* Strategies List */}
          {strategiesLoading ? (
            <div className="space-y-4">
              <CardSkeleton /><CardSkeleton /><CardSkeleton />
            </div>
          ) : strategiesError ? (
            <ErrorMessage error={strategiesError} onRetry={refetchStrategies} />
          ) : !strategies?.length ? (
            <div className="bg-navy-800 border border-navy-600 rounded-xl p-12 text-center">
              <div className="w-16 h-16 rounded-2xl bg-navy-700 flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2L2 7l10 5 10-5-10-5z" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M2 17l10 5 10-5" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M2 12l10 5 10-5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-slate-300 mb-2">No Strategies Yet</h3>
              <p className="text-sm text-slate-500 mb-6">Create your first strategy by describing it in plain English</p>
              <button
                onClick={() => handleStartCreate('')}
                className="px-6 py-2.5 bg-accent hover:bg-accent-light text-navy-900 font-medium text-sm rounded-lg transition-colors"
              >
                Create Strategy
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {strategies.map((strategy) => (
                <StrategyListItem
                  key={strategy.id}
                  strategy={strategy}
                  onView={() => handleViewDetail(strategy)}
                  onEdit={() => handleEdit(strategy)}
                  onToggle={() => handleToggleStrategy(strategy)}
                  onDelete={() => handleDeleteStrategy(strategy)}
                />
              ))}
            </div>
          )}

          {/* Templates */}
          {templates?.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-slate-200 mb-4">Strategy Templates</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {templates.map((template) => (
                  <button
                    key={template.id}
                    onClick={() => handleStartCreate(template.description)}
                    className="bg-navy-800 border border-navy-600 rounded-xl p-5 text-left hover:border-accent/30 transition-colors"
                  >
                    <h4 className="font-semibold text-slate-200 mb-1">{template.name}</h4>
                    <p className="text-sm text-slate-400 line-clamp-2">{template.description}</p>
                    <div className="mt-3 text-xs text-accent">Use template</div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* CREATE VIEW */}
      {view === VIEWS.CREATE && (
        <div className="space-y-6 max-w-4xl">
          <Card>
            <h3 className="text-lg font-semibold text-slate-100 mb-4">
              {editingStrategy ? 'Edit Strategy' : 'Describe Your Strategy'}
            </h3>
            <p className="text-sm text-slate-400 mb-4">
              Write your strategy in plain English. Our AI will parse it into actionable entry/exit conditions.
            </p>

            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., Buy 1 lot Nifty ATM CE when spot price crosses above VWAP, with target of 30% and stop loss of 20%..."
              rows={5}
              className="w-full bg-navy-700 border border-navy-600 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-accent/50 resize-none"
            />

            <div className="flex items-center justify-between mt-4">
              <div className="text-xs text-slate-500">
                {description.length > 0 ? `${description.length} characters` : 'Describe entry conditions, position sizing, and exit rules'}
              </div>
              <button
                onClick={handleParse}
                disabled={!description.trim() || parseLoading}
                className="flex items-center gap-2 px-6 py-2.5 bg-accent hover:bg-accent-light text-navy-900 font-medium text-sm rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {parseLoading ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeDasharray="32" strokeLinecap="round" />
                    </svg>
                    Parsing...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="3" />
                      <path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
                    </svg>
                    Parse Strategy
                  </>
                )}
              </button>
            </div>
          </Card>

          {parseError && (
            <div className="p-4 bg-negative/10 border border-negative/30 rounded-xl text-sm text-negative">
              {parseError}
            </div>
          )}

          {parsedResult && (
            <>
              <ParsedStrategy
                strategy={parsedResult}
                onConfirm={handleConfirmStrategy}
                onEdit={() => setParsedResult(null)}
                confirmLabel={editingStrategy ? 'Update Strategy' : 'Confirm & Save Strategy'}
              />
              {actionError && (
                <div className="p-4 bg-negative/10 border border-negative/30 rounded-xl text-sm text-negative">
                  {actionError}
                </div>
              )}
              {actionLoading && (
                <div className="flex items-center justify-center gap-2 text-sm text-slate-400">
                  <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeDasharray="32" strokeLinecap="round" />
                  </svg>
                  Saving strategy...
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* DETAIL VIEW */}
      {view === VIEWS.DETAIL && selectedStrategy && (
        <div className="space-y-6 max-w-4xl">
          <Card className="border-2 border-accent/20">
            <div className="flex items-start justify-between mb-6">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <h2 className="text-xl font-semibold text-slate-100">{selectedStrategy.name}</h2>
                  <span className={`text-xs font-medium px-2 py-1 rounded ${
                    selectedStrategy.status === 'active'
                      ? 'bg-positive/20 text-positive'
                      : selectedStrategy.status === 'paused'
                        ? 'bg-warning/20 text-warning'
                        : 'bg-slate-500/20 text-slate-400'
                  }`}>
                    {selectedStrategy.status?.toUpperCase() || 'DRAFT'}
                  </span>
                </div>
                <p className="text-sm text-slate-400">{selectedStrategy.description}</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleEdit(selectedStrategy)}
                  className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 bg-navy-700 hover:bg-navy-600 rounded-lg transition-colors"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleToggleStrategy(selectedStrategy)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                    selectedStrategy.status === 'active'
                      ? 'bg-warning/10 text-warning hover:bg-warning/20'
                      : 'bg-positive/10 text-positive hover:bg-positive/20'
                  }`}
                >
                  {selectedStrategy.status === 'active' ? 'Pause' : 'Activate'}
                </button>
              </div>
            </div>

            {/* Entry Conditions */}
            {(selectedStrategy.entry_conditions?.length > 0 || selectedStrategy.entryConditions?.length > 0) && (
              <div className="mb-6">
                <div className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-3">Entry Conditions</div>
                <div className="flex flex-wrap gap-2">
                  {(selectedStrategy.entry_conditions || selectedStrategy.entryConditions || []).map((condition, idx) => (
                    <ConditionBadge key={idx} condition={condition} type="entry" />
                  ))}
                </div>
              </div>
            )}

            {/* Action */}
            {selectedStrategy.action && (
              <div className="mb-6">
                <div className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-3">Action</div>
                <div className="flex items-center gap-3">
                  <span className={`px-3 py-1.5 rounded-lg text-sm font-semibold ${
                    selectedStrategy.action?.type === 'BUY'
                      ? 'bg-positive/20 text-positive'
                      : 'bg-negative/20 text-negative'
                  }`}>
                    {selectedStrategy.action?.type}
                  </span>
                  <span className="text-slate-200 font-medium">
                    {selectedStrategy.action?.quantity} lot{selectedStrategy.action?.quantity > 1 ? 's' : ''}
                  </span>
                  <span className="text-slate-300">
                    {selectedStrategy.action?.instrument} {selectedStrategy.action?.strikeSelection} {selectedStrategy.action?.optionType}
                  </span>
                </div>
              </div>
            )}

            {/* Exit Conditions */}
            {(selectedStrategy.exit_conditions?.length > 0 || selectedStrategy.exitConditions?.length > 0) && (
              <div className="mb-6">
                <div className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-3">Exit Conditions</div>
                <div className="flex flex-wrap gap-2">
                  {(selectedStrategy.exit_conditions || selectedStrategy.exitConditions || []).map((condition, idx) => (
                    <ConditionBadge key={idx} condition={condition} type="exit" />
                  ))}
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="pt-4 border-t border-navy-700 text-xs text-slate-500">
              <span>Created {timeAgo(selectedStrategy.created_at || selectedStrategy.createdAt)}</span>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}

function StrategyListItem({ strategy, onView, onEdit, onToggle, onDelete }) {
  const entryConditions = strategy.entry_conditions || strategy.entryConditions || []
  const exitConditions = strategy.exit_conditions || strategy.exitConditions || []

  return (
    <div className="bg-navy-800 border border-navy-600 rounded-xl p-5 hover:border-navy-500 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 cursor-pointer" onClick={onView}>
          <div className="flex items-center gap-3 mb-1">
            <h3 className="font-semibold text-slate-200">{strategy.name}</h3>
            <span className={`text-xs font-medium px-2 py-0.5 rounded ${
              strategy.status === 'active'
                ? 'bg-positive/20 text-positive'
                : strategy.status === 'paused'
                  ? 'bg-warning/20 text-warning'
                  : 'bg-slate-500/20 text-slate-400'
            }`}>
              {strategy.status?.toUpperCase() || 'DRAFT'}
            </span>
          </div>
          <p className="text-sm text-slate-400 line-clamp-1">{strategy.description}</p>
        </div>
        <div className="flex items-center gap-1 ml-4">
          <button
            onClick={onToggle}
            className={`p-2 rounded-lg transition-colors ${
              strategy.status === 'active'
                ? 'text-positive hover:bg-positive/10'
                : 'text-slate-500 hover:bg-navy-700'
            }`}
            title={strategy.status === 'active' ? 'Pause' : 'Activate'}
          >
            {strategy.status === 'active' ? (
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="6" y="4" width="4" height="16" rx="1" />
                <rect x="14" y="4" width="4" height="16" rx="1" />
              </svg>
            ) : (
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5,3 19,12 5,21" />
              </svg>
            )}
          </button>
          <button
            onClick={onEdit}
            className="p-2 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-navy-700 transition-colors"
            title="Edit"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
          </button>
          <button
            onClick={onDelete}
            className="p-2 rounded-lg text-slate-500 hover:text-negative hover:bg-negative/10 transition-colors"
            title="Delete"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
            </svg>
          </button>
        </div>
      </div>

      {/* Conditions preview */}
      <div className="flex flex-wrap gap-1.5 mt-3">
        {entryConditions.slice(0, 3).map((c, i) => (
          <ConditionBadge key={`e-${i}`} condition={c} type="entry" />
        ))}
        {exitConditions.slice(0, 2).map((c, i) => (
          <ConditionBadge key={`x-${i}`} condition={c} type="exit" />
        ))}
        {entryConditions.length + exitConditions.length > 5 && (
          <span className="text-xs text-slate-500 px-2 py-2">
            +{entryConditions.length + exitConditions.length - 5} more
          </span>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-navy-700 text-xs text-slate-500">
        <span>{timeAgo(strategy.created_at || strategy.createdAt)}</span>
        {strategy.action && (
          <span>
            {strategy.action.type} {strategy.action.quantity} lot{strategy.action.quantity > 1 ? 's' : ''} {strategy.action.instrument}
          </span>
        )}
      </div>
    </div>
  )
}
