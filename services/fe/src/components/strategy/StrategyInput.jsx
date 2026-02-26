import { useState } from 'react'
import Card, { CardHeader } from '../common/Card'
import { parseStrategy, getTemplateCategories } from '../../api/strategies'
import { useApi } from '../../hooks/useApi'

export default function StrategyInput({ onStrategyParsed, isLoading, setIsLoading, initialValue = '' }) {
  const [input, setInput] = useState(initialValue)
  const [error, setError] = useState(null)
  const [selectedCategory, setSelectedCategory] = useState(null)

  const { data: categories } = useApi(() => getTemplateCategories(), [])

  const STRATEGY_CATEGORIES = categories || []

  const handleParse = async () => {
    if (!input.trim()) return

    setIsLoading(true)
    setError(null)

    try {
      const data = await parseStrategy(input.trim())

      if (data.error) {
        setError(data.error)
        return
      }

      // Add original input to the parsed strategy
      onStrategyParsed({
        ...data,
        originalInput: input.trim()
      })
    } catch (err) {
      console.error('Parse error:', err)
      setError('Failed to parse strategy. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleExampleClick = (template) => {
    setInput(template)
    setSelectedCategory(null)
  }

  const handleCategoryClick = (categoryName) => {
    setSelectedCategory(selectedCategory === categoryName ? null : categoryName)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && e.metaKey) {
      handleParse()
    }
  }

  return (
    <Card>
      <CardHeader
        title="Describe Your Strategy"
        subtitle="Use natural language to define entry conditions, actions, and exit rules"
      />

      <div className="space-y-4">
        {/* Input Area */}
        <div className="relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Example: Buy 1 lot Nifty CE when Nifty is 100 points up from day's low and OI is increasing. Exit at 20% profit or 10% loss."
            className="w-full h-32 px-4 py-3 bg-navy-700 border border-navy-600 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent resize-none"
            disabled={isLoading}
          />
          <div className="absolute bottom-3 right-3 text-xs text-slate-500">
            ⌘ + Enter to parse
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="px-4 py-3 bg-negative/10 border border-negative/30 rounded-lg text-negative text-sm">
            {error}
          </div>
        )}

        {/* Parse Button */}
        <div className="flex items-center justify-between">
          <div className="text-xs text-slate-500">
            Supports: Price levels, OI, RSI, Moving Averages, Time filters, Target/Stoploss
          </div>
          <button
            onClick={handleParse}
            disabled={!input.trim() || isLoading}
            className="flex items-center gap-2 px-6 py-2.5 bg-accent hover:bg-accent-light disabled:bg-navy-600 disabled:text-slate-500 text-navy-900 font-medium rounded-lg transition-colors"
          >
            {isLoading ? (
              <>
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Parsing...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Parse with AI
              </>
            )}
          </button>
        </div>

        {/* Strategy Templates */}
        <div className="pt-4 border-t border-navy-600">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-sm font-medium text-slate-300">Strategy Templates</div>
              <div className="text-xs text-slate-500 mt-0.5">Click a category to explore pre-built strategies</div>
            </div>
            <div className="text-xs text-slate-500">
              {(categories || []).reduce((acc, cat) => acc + cat.strategies.length, 0)} templates available
            </div>
          </div>

          {/* Category Pills */}
          <div className="flex flex-wrap gap-2 mb-4">
            {STRATEGY_CATEGORIES.map((category) => (
              <button
                key={category.name}
                onClick={() => handleCategoryClick(category.name)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  selectedCategory === category.name
                    ? `${category.bgColor} ${category.color} border ${category.borderColor}`
                    : 'bg-navy-700/50 text-slate-400 hover:bg-navy-700 hover:text-slate-300 border border-transparent'
                }`}
              >
                <span>{category.icon}</span>
                <span>{category.name}</span>
                <span className={`text-xs px-1.5 py-0.5 rounded ${
                  selectedCategory === category.name
                    ? 'bg-white/10'
                    : 'bg-navy-600'
                }`}>
                  {category.strategies.length}
                </span>
              </button>
            ))}
          </div>

          {/* Expanded Category Strategies */}
          {selectedCategory && (
            <div className="space-y-2 animate-in fade-in slide-in-from-top-2 duration-200">
              {STRATEGY_CATEGORIES.find(c => c.name === selectedCategory)?.strategies.map((strategy, idx) => {
                const category = STRATEGY_CATEGORIES.find(c => c.name === selectedCategory)
                return (
                  <button
                    key={idx}
                    onClick={() => handleExampleClick(strategy.template)}
                    className={`w-full text-left p-4 rounded-lg border transition-all hover:scale-[1.01] ${category.bgColor} ${category.borderColor} border hover:border-opacity-60`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className={`font-medium ${category.color}`}>
                          {strategy.title}
                        </div>
                        <div className="text-xs text-slate-400 mt-1">
                          {strategy.description}
                        </div>
                        <div className="text-xs text-slate-500 mt-2 line-clamp-2">
                          "{strategy.template}"
                        </div>
                      </div>
                      <div className="flex-shrink-0">
                        <svg className={`w-5 h-5 ${category.color} opacity-50`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
          )}

          {/* Quick Start Hint */}
          {!selectedCategory && (
            <div className="text-center py-6 text-slate-500 text-sm">
              <div className="flex items-center justify-center gap-2 mb-2">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Select a category above or write your own strategy</span>
              </div>
              <div className="text-xs text-slate-600">
                You can combine multiple conditions like price levels, indicators, time filters, and risk parameters
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}
