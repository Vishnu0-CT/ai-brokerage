import { useState, useEffect, useMemo } from 'react'
import { useApi } from '../hooks/useApi'
import { useOptionChainWebSocket } from '../hooks/useOptionChainWebSocket'
import { useWatchlistPriceStream } from '../hooks/useWatchlistPriceStream'
import { getWatchlist } from '../api/watchlist'
import { getExpiries } from '../api/optionChain'
import { createPosition } from '../api/positions'
import { placeOrder } from '../api/orders'
import { getHoldings } from '../api/portfolio'
import { formatINR, getPnlColor } from '../utils/formatters'
import { CardSkeleton, TableSkeleton } from '../components/common/Skeleton'
import ErrorMessage from '../components/common/ErrorMessage'

export default function Trade() {
  const [selectedSymbol, setSelectedSymbol] = useState(null)
  const [selectedExpiry, setSelectedExpiry] = useState(null)
  const [selectedStrike, setSelectedStrike] = useState(null)
  const [orderSide, setOrderSide] = useState(null)
  const [orderType, setOrderType] = useState('MARKET')
  const [quantity, setQuantity] = useState(1)
  const [showOrderModal, setShowOrderModal] = useState(false)
  const [orderLoading, setOrderLoading] = useState(false)
  const [orderError, setOrderError] = useState(null)
  const [orderSuccess, setOrderSuccess] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [tradeMode, setTradeMode] = useState('OPTIONS')
  const [spotQuantity, setSpotQuantity] = useState(1)
  const [spotSide, setSpotSide] = useState('buy')

  const { data: watchlist, loading: watchlistLoading, error: watchlistError, refetch: refetchWatchlist } = useApi(() => getWatchlist(), [])
  const { data: holdings, refetch: refetchHoldings } = useApi(() => getHoldings(), [])
  const { data: expiries, loading: expiriesLoading } = useApi(() => getExpiries(), [])

  // Real-time price updates for watchlist
  const { priceUpdates } = useWatchlistPriceStream(true)

  // Use WebSocket for real-time option chain updates
  const { data: optionChain, loading: chainLoading, error: chainError, connected: wsConnected } = useOptionChainWebSocket(
    selectedSymbol?.symbol,
    selectedExpiry?.date,
    !!(selectedSymbol && selectedExpiry)
  )

  // Set default expiry when expiries load
  useEffect(() => {
    if (expiries?.length > 0 && !selectedExpiry) {
      setSelectedExpiry(expiries[0])
    }
  }, [expiries]) // eslint-disable-line react-hooks/exhaustive-deps

  // Update selectedSymbol with real-time prices
  useEffect(() => {
    if (selectedSymbol && priceUpdates[selectedSymbol.symbol]) {
      const priceUpdate = priceUpdates[selectedSymbol.symbol]
      setSelectedSymbol(prev => ({
        ...prev,
        price: priceUpdate.price,
        change: priceUpdate.change,
        change_percent: priceUpdate.change_percent,
        high: priceUpdate.high ?? prev.high,
        low: priceUpdate.low ?? prev.low,
      }))
    }
  }, [priceUpdates, selectedSymbol?.symbol]) // eslint-disable-line react-hooks/exhaustive-deps

  // Merge watchlist with real-time price updates
  const watchlistWithPrices = useMemo(() => {
    if (!watchlist) return []
    return watchlist.map(item => {
      const priceUpdate = priceUpdates[item.symbol]
      if (priceUpdate) {
        return {
          ...item,
          price: priceUpdate.price,
          change: priceUpdate.change,
          change_percent: priceUpdate.change_percent,
          high: priceUpdate.high ?? item.high,
          low: priceUpdate.low ?? item.low,
        }
      }
      return item
    })
  }, [watchlist, priceUpdates])

  const filteredWatchlist = useMemo(() => {
    if (!watchlistWithPrices) return []
    if (!searchTerm) return watchlistWithPrices
    const term = searchTerm.toLowerCase()
    return watchlistWithPrices.filter(item =>
      item.symbol.toLowerCase().includes(term) ||
      item.type?.toLowerCase().includes(term)
    )
  }, [watchlistWithPrices, searchTerm])

  const handleSelectSymbol = (item) => {
    setSelectedSymbol(item)
    setSpotQuantity(1)
    // INDEX instruments (NIFTY, BANKNIFTY, FINNIFTY) can't be traded as spot
    if (item.type === 'INDEX') {
      setTradeMode('OPTIONS')
    }
  }

  const handleSelectStrike = (strike, side) => {
    setSelectedStrike(strike)
    setOrderSide(side)
    setQuantity(1)
    setOrderType('MARKET')
    setOrderError(null)
    setOrderSuccess(null)
    setShowOrderModal(true)
  }

  const handlePlaceOrder = async () => {
    if (!selectedStrike || !orderSide || !selectedSymbol || !selectedExpiry) return

    setOrderLoading(true)
    setOrderError(null)

    const optionType = orderSide === 'BUY_CALL' || orderSide === 'SELL_CALL' ? 'CE' : 'PE'
    const direction = orderSide.startsWith('BUY') ? 'BUY' : 'SELL'
    const strikeData = optionType === 'CE' ? selectedStrike.call : selectedStrike.put
    const premium = orderType === 'MARKET' ? strikeData?.ltp : (strikeData?.ask || strikeData?.ltp)
    const fullSymbol = `${selectedSymbol.symbol} ${selectedStrike.strike} ${optionType}`

    try {
      await createPosition({
        symbol: fullSymbol,
        order_type: direction,
        quantity: quantity * selectedSymbol.lot_size,
        lots: quantity,
        price: premium,
        expiry: selectedExpiry.date,
      })
      setOrderSuccess(`${direction} ${quantity} lot${quantity > 1 ? 's' : ''} of ${selectedSymbol.symbol} ${selectedStrike.strike} ${optionType}`)
      setTimeout(() => {
        setShowOrderModal(false)
        setOrderSuccess(null)
      }, 2000)
    } catch (err) {
      setOrderError(err.message || 'Failed to place order')
    } finally {
      setOrderLoading(false)
    }
  }

  const handlePlaceSpotOrder = async () => {
    if (!selectedSymbol || !spotSide) return

    setOrderLoading(true)
    setOrderError(null)

    try {
      await placeOrder({
        symbol: selectedSymbol.symbol,
        side: spotSide,
        quantity: spotQuantity,
        price: selectedSymbol.price || 0,
      })
      setOrderSuccess(`${spotSide.toUpperCase()} ${spotQuantity} share${spotQuantity > 1 ? 's' : ''} of ${selectedSymbol.symbol}`)
      refetchHoldings()
      setTimeout(() => {
        setShowOrderModal(false)
        setOrderSuccess(null)
      }, 2000)
    } catch (err) {
      setOrderError(err.message || 'Failed to place order')
    } finally {
      setOrderLoading(false)
    }
  }

  // Use real-time spot price from WebSocket when available, fallback to watchlist price
  const spotPrice = optionChain?.spot_price || selectedSymbol?.price || 0

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-semibold text-slate-100">Trade</h1>
        <p className="text-sm text-slate-500 mt-1">Spot and options trading</p>
      </div>

      <div className="flex gap-6">
        {/* Watchlist Sidebar */}
        <div className="w-80 flex-shrink-0">
          <div className="bg-navy-800 border border-navy-600 rounded-xl overflow-hidden">
            {/* Search */}
            <div className="p-3 border-b border-navy-700">
              <div className="relative">
                <svg className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8" />
                  <path d="m21 21-4.35-4.35" strokeLinecap="round" />
                </svg>
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search instruments..."
                  className="w-full bg-navy-700 border border-navy-600 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-accent/50"
                />
              </div>
            </div>

            {/* Watchlist items */}
            <div className="max-h-[calc(100vh-280px)] overflow-y-auto">
              {watchlistLoading ? (
                <div className="p-4 space-y-3">
                  <CardSkeleton /><CardSkeleton /><CardSkeleton />
                </div>
              ) : watchlistError ? (
                <div className="p-4">
                  <ErrorMessage error={watchlistError} onRetry={refetchWatchlist} />
                </div>
              ) : filteredWatchlist.length === 0 ? (
                <div className="p-8 text-center text-sm text-slate-500">
                  {searchTerm ? 'No matching instruments' : 'Watchlist is empty'}
                </div>
              ) : (
                filteredWatchlist.map((item) => {
                  const isSelected = selectedSymbol?.symbol === item.symbol
                  const changeColor = getPnlColor(item.change || 0)

                  return (
                    <button
                      key={item.symbol}
                      onClick={() => handleSelectSymbol(item)}
                      className={`w-full text-left px-4 py-3 border-b border-navy-700/50 hover:bg-navy-700/50 transition-colors ${
                        isSelected ? 'bg-accent/10 border-l-2 border-l-accent' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-sm font-medium text-slate-200">{item.symbol}</div>
                          <div className="text-xs text-slate-500">
                            {item.type} {item.lot_size ? `| Lot: ${item.lot_size}` : ''}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-mono text-sm text-slate-200">{formatINR(item.price || 0)}</div>
                          <div className={`font-mono text-xs ${changeColor}`}>
                            {item.change >= 0 ? '+' : ''}{item.change?.toFixed(2) || '0.00'} ({item.change_percent?.toFixed(2) || '0.00'}%)
                          </div>
                        </div>
                      </div>
                      {/* Day range */}
                      {item.high && item.low && (
                        <div className="mt-2">
                          <div className="flex items-center justify-between text-xs text-slate-600 mb-1">
                            <span>{formatINR(item.low)}</span>
                            <span>{formatINR(item.high)}</span>
                          </div>
                          <div className="h-1 bg-navy-600 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-accent/50 rounded-full"
                              style={{
                                width: `${item.high - item.low > 0 ? ((item.price - item.low) / (item.high - item.low)) * 100 : 50}%`,
                              }}
                            />
                          </div>
                        </div>
                      )}
                    </button>
                  )
                })
              )}
            </div>
          </div>
        </div>

        {/* Option Chain */}
        <div className="flex-1 min-w-0">
          {!selectedSymbol ? (
            <div className="bg-navy-800 border border-navy-600 rounded-xl p-12 text-center">
              <div className="w-16 h-16 rounded-2xl bg-navy-700 flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M3 3v18h18" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M7 12l4-4 4 4 6-6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-slate-300 mb-2">Select an Instrument</h3>
              <p className="text-sm text-slate-500">Choose a symbol from the watchlist to view its option chain</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Instrument header */}
              <div className="bg-navy-800 border border-navy-600 rounded-xl p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-100">{selectedSymbol.symbol}</h2>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="font-mono text-xl text-slate-200">{formatINR(spotPrice)}</span>
                      <span className={`font-mono text-sm ${getPnlColor(selectedSymbol.change || 0)}`}>
                        {selectedSymbol.change >= 0 ? '+' : ''}{selectedSymbol.change?.toFixed(2) || '0.00'} ({selectedSymbol.change_percent?.toFixed(2) || '0.00'}%)
                      </span>
                      {/* Real-time connection indicator */}
                      {tradeMode === 'OPTIONS' && (
                        <span className="flex items-center gap-1.5 text-xs">
                          <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-positive animate-pulse' : 'bg-slate-600'}`} />
                          <span className="text-slate-500">{wsConnected ? 'Live' : 'Connecting...'}</span>
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-8">
                    {/* Expiry selector — only in OPTIONS mode */}
                    {tradeMode === 'OPTIONS' && (
                      <div className="flex items-center gap-2">
                        {expiriesLoading ? (
                          <div className="h-8 w-48 bg-navy-700 rounded-lg animate-pulse" />
                        ) : (
                          <div className="flex flex-wrap gap-1.5">
                            {expiries?.slice(0, 6).map((exp) => (
                              <button
                                key={exp.date}
                                onClick={() => setSelectedExpiry(exp)}
                                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                                  selectedExpiry?.date === exp.date
                                    ? 'bg-accent text-navy-900'
                                    : 'bg-navy-700 text-slate-400 hover:bg-navy-600'
                                }`}
                              >
                                {exp.label}
                                {!exp.is_weekly && (
                                  <span className="ml-1 text-[10px] opacity-60">M</span>
                                )}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Spot / Options toggle — only for STOCK instruments */}
                    {selectedSymbol.type === 'STOCK' && (
                      <div className="flex gap-1.5 border border-navy-600 rounded-lg p-1">
                        {['SPOT', 'OPTIONS'].map((mode) => (
                          <button
                            key={mode}
                            onClick={() => setTradeMode(mode)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                              tradeMode === mode
                                ? 'bg-accent text-navy-900'
                                : 'bg-navy-700 text-slate-400 hover:bg-navy-600'
                            }`}
                          >
                            {mode === 'SPOT' ? 'Spot' : 'Options'}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {tradeMode === 'SPOT' ? (() => {
                const bid = selectedSymbol.bid || spotPrice * 0.9995
                const ask = selectedSymbol.ask || spotPrice * 1.0005
                const hasHolding = holdings?.find(h => h.symbol === selectedSymbol.symbol)
                const rangePercent = selectedSymbol.high && selectedSymbol.low && selectedSymbol.high - selectedSymbol.low > 0
                  ? ((spotPrice - selectedSymbol.low) / (selectedSymbol.high - selectedSymbol.low)) * 100
                  : 50

                return (
                  <div className="bg-navy-800 border border-navy-600 rounded-xl p-6 space-y-6">
                    {/* Price section */}
                    <div className="text-center">
                      <div className="font-mono text-3xl font-semibold text-slate-100">{formatINR(spotPrice)}</div>
                      <div className={`font-mono text-sm mt-1 ${getPnlColor(selectedSymbol.change || 0)}`}>
                        {selectedSymbol.change >= 0 ? '+' : ''}{selectedSymbol.change?.toFixed(2) || '0.00'} ({selectedSymbol.change_percent?.toFixed(2) || '0.00'}%)
                      </div>
                    </div>

                    {/* Day range bar */}
                    {selectedSymbol.high && selectedSymbol.low && (
                      <div>
                        <div className="text-xs text-slate-500 mb-2">Day Range</div>
                        <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                          <span className="font-mono">{formatINR(selectedSymbol.low)}</span>
                          <span className="font-mono">{formatINR(selectedSymbol.high)}</span>
                        </div>
                        <div className="relative h-2 bg-navy-600 rounded-full overflow-hidden">
                          <div className="h-full bg-accent/40 rounded-full" style={{ width: `${rangePercent}%` }} />
                          <div
                            className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-accent rounded-full border-2 border-navy-800"
                            style={{ left: `${rangePercent}%`, transform: `translate(-50%, -50%)` }}
                          />
                        </div>
                      </div>
                    )}

                    {/* Bid / Ask */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3 bg-navy-700/50 rounded-lg text-center">
                        <div className="text-xs text-slate-500 mb-1">Bid</div>
                        <div className="font-mono text-sm text-positive">{bid.toFixed(2)}</div>
                      </div>
                      <div className="p-3 bg-navy-700/50 rounded-lg text-center">
                        <div className="text-xs text-slate-500 mb-1">Ask</div>
                        <div className="font-mono text-sm text-negative">{ask.toFixed(2)}</div>
                      </div>
                    </div>

                    {/* Volume */}
                    {selectedSymbol.volume != null && (
                      <div className="flex items-center justify-between p-3 bg-navy-700/50 rounded-lg">
                        <span className="text-sm text-slate-400">Volume</span>
                        <span className="font-mono text-sm text-slate-200">{selectedSymbol.volume.toLocaleString('en-IN')}</span>
                      </div>
                    )}

                    {/* Quantity input */}
                    <div>
                      <label className="text-xs text-slate-500 mb-2 block">Quantity (Shares)</label>
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => setSpotQuantity(Math.max(1, spotQuantity - 1))}
                          className="w-10 h-10 rounded-lg bg-navy-700 text-slate-300 hover:bg-navy-600 flex items-center justify-center"
                        >
                          -
                        </button>
                        <input
                          type="number"
                          value={spotQuantity}
                          onChange={(e) => setSpotQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                          className="flex-1 bg-navy-700 border border-navy-600 rounded-lg px-4 py-2 text-center font-mono text-slate-200 outline-none focus:border-accent/50"
                          min="1"
                        />
                        <button
                          onClick={() => setSpotQuantity(spotQuantity + 1)}
                          className="w-10 h-10 rounded-lg bg-navy-700 text-slate-300 hover:bg-navy-600 flex items-center justify-center"
                        >
                          +
                        </button>
                      </div>
                    </div>

                    {/* Estimated value */}
                    <div className="p-3 bg-navy-700/50 rounded-lg border border-navy-600">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-slate-400">Estimated Value</span>
                        <span className="font-mono text-lg font-semibold text-slate-200">{formatINR(spotPrice * spotQuantity)}</span>
                      </div>
                    </div>

                    {/* BUY / SELL buttons */}
                    <div className="grid grid-cols-2 gap-3">
                      <button
                        onClick={() => { setSpotSide('buy'); setOrderError(null); setOrderSuccess(null); setShowOrderModal(true) }}
                        className="py-3 rounded-xl text-sm font-semibold bg-positive hover:bg-positive/80 text-navy-900 transition-colors"
                      >
                        BUY
                      </button>
                      <button
                        onClick={() => { setSpotSide('sell'); setOrderError(null); setOrderSuccess(null); setShowOrderModal(true) }}
                        disabled={!hasHolding}
                        className={`py-3 rounded-xl text-sm font-semibold transition-colors ${
                          hasHolding
                            ? 'bg-negative hover:bg-negative/80 text-white'
                            : 'bg-navy-700 text-slate-600 cursor-not-allowed'
                        }`}
                      >
                        SELL
                      </button>
                    </div>
                  </div>
                )
              })() : (
                <>
                  {/* Option chain table */}
                  {chainLoading ? (
                    <TableSkeleton rows={10} />
                  ) : chainError ? (
                    <ErrorMessage error={chainError} />
                  ) : !optionChain?.strikes?.length ? (
                    <div className="bg-navy-800 border border-navy-600 rounded-xl p-8 text-center text-sm text-slate-500">
                      No option chain data available
                    </div>
                  ) : (
                    <div className="bg-navy-800 border border-navy-600 rounded-xl overflow-hidden">
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-navy-700">
                              <th colSpan="5" className="px-3 py-3 text-center text-xs font-medium text-positive uppercase tracking-wide bg-positive/5">
                                CALLS
                              </th>
                              <th className="px-3 py-3 text-center text-xs font-medium text-slate-400 uppercase tracking-wide bg-navy-700/50">
                                Strike
                              </th>
                              <th colSpan="5" className="px-3 py-3 text-center text-xs font-medium text-negative uppercase tracking-wide bg-negative/5">
                                PUTS
                              </th>
                            </tr>
                            <tr className="border-b border-navy-700 text-xs text-slate-500">
                              <th className="px-2 py-2 text-right font-medium">OI</th>
                              <th className="px-2 py-2 text-right font-medium">Chg</th>
                              <th className="px-2 py-2 text-right font-medium">LTP</th>
                              <th className="px-2 py-2 text-center font-medium">B</th>
                              <th className="px-2 py-2 text-center font-medium">S</th>
                              <th className="px-2 py-2 text-center font-medium bg-navy-700/50">Price</th>
                              <th className="px-2 py-2 text-center font-medium">B</th>
                              <th className="px-2 py-2 text-center font-medium">S</th>
                              <th className="px-2 py-2 text-right font-medium">LTP</th>
                              <th className="px-2 py-2 text-right font-medium">Chg</th>
                              <th className="px-2 py-2 text-right font-medium">OI</th>
                            </tr>
                          </thead>
                          <tbody>
                            {optionChain.strikes.map((strike) => {
                              const isATM = Math.abs(strike.strike - spotPrice) <= (optionChain.step_size || 50) / 2
                              const isITMCall = strike.strike < spotPrice
                              const isITMPut = strike.strike > spotPrice

                              return (
                                <tr
                                  key={strike.strike}
                                  className={`border-b border-navy-700/50 hover:bg-navy-700/30 transition-colors ${
                                    isATM ? 'bg-accent/5 border-l-2 border-l-accent' : ''
                                  }`}
                                >
                                  {/* Call side */}
                                  <td className={`px-2 py-2 text-right font-mono text-xs ${isITMCall ? 'bg-positive/5' : ''}`}>
                                    {strike.call?.oi?.toLocaleString('en-IN') || '-'}
                                  </td>
                                  <td className={`px-2 py-2 text-right font-mono text-xs ${
                                    (strike.call?.change || 0) >= 0 ? 'text-positive' : 'text-negative'
                                  } ${isITMCall ? 'bg-positive/5' : ''}`}>
                                    {strike.call?.change?.toFixed(2) || '-'}
                                  </td>
                                  <td className={`px-2 py-2 text-right font-mono text-sm font-medium text-slate-200 ${isITMCall ? 'bg-positive/5' : ''}`}>
                                    {strike.call?.ltp?.toFixed(2) || '-'}
                                  </td>
                                  <td className={`px-2 py-2 text-center ${isITMCall ? 'bg-positive/5' : ''}`}>
                                    <button
                                      onClick={() => handleSelectStrike(strike, 'BUY_CALL')}
                                      className="w-7 h-7 rounded bg-positive/10 text-positive hover:bg-positive/20 text-xs font-bold transition-colors"
                                    >
                                      B
                                    </button>
                                  </td>
                                  <td className={`px-2 py-2 text-center ${isITMCall ? 'bg-positive/5' : ''}`}>
                                    <button
                                      onClick={() => handleSelectStrike(strike, 'SELL_CALL')}
                                      className="w-7 h-7 rounded bg-negative/10 text-negative hover:bg-negative/20 text-xs font-bold transition-colors"
                                    >
                                      S
                                    </button>
                                  </td>

                                  {/* Strike */}
                                  <td className="px-2 py-2 text-center bg-navy-700/50">
                                    <span className={`font-mono text-sm font-semibold ${isATM ? 'text-accent' : 'text-slate-300'}`}>
                                      {strike.strike}
                                    </span>
                                  </td>

                                  {/* Put side */}
                                  <td className={`px-2 py-2 text-center ${isITMPut ? 'bg-negative/5' : ''}`}>
                                    <button
                                      onClick={() => handleSelectStrike(strike, 'BUY_PUT')}
                                      className="w-7 h-7 rounded bg-positive/10 text-positive hover:bg-positive/20 text-xs font-bold transition-colors"
                                    >
                                      B
                                    </button>
                                  </td>
                                  <td className={`px-2 py-2 text-center ${isITMPut ? 'bg-negative/5' : ''}`}>
                                    <button
                                      onClick={() => handleSelectStrike(strike, 'SELL_PUT')}
                                      className="w-7 h-7 rounded bg-negative/10 text-negative hover:bg-negative/20 text-xs font-bold transition-colors"
                                    >
                                      S
                                    </button>
                                  </td>
                                  <td className={`px-2 py-2 text-right font-mono text-sm font-medium text-slate-200 ${isITMPut ? 'bg-negative/5' : ''}`}>
                                    {strike.put?.ltp?.toFixed(2) || '-'}
                                  </td>
                                  <td className={`px-2 py-2 text-right font-mono text-xs ${
                                    (strike.put?.change || 0) >= 0 ? 'text-positive' : 'text-negative'
                                  } ${isITMPut ? 'bg-negative/5' : ''}`}>
                                    {strike.put?.change?.toFixed(2) || '-'}
                                  </td>
                                  <td className={`px-2 py-2 text-right font-mono text-xs ${isITMPut ? 'bg-negative/5' : ''}`}>
                                    {strike.put?.oi?.toLocaleString('en-IN') || '-'}
                                  </td>
                                </tr>
                              )
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Order Modal */}
      {showOrderModal && (tradeMode === 'SPOT' || selectedStrike) && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowOrderModal(false)}>
          <div className="bg-navy-800 border border-navy-600 rounded-2xl w-[480px] max-w-[90vw] p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-slate-100">Place Order</h3>
              <button onClick={() => setShowOrderModal(false)} className="text-slate-500 hover:text-slate-300">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" />
                </svg>
              </button>
            </div>

            {orderSuccess ? (
              <div className="text-center py-8">
                <div className="w-16 h-16 rounded-full bg-positive/20 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-positive" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <p className="text-sm text-positive">{orderSuccess}</p>
              </div>
            ) : tradeMode === 'SPOT' ? (
              <>
                {/* Spot order details */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-navy-700/50 rounded-lg">
                    <span className="text-sm text-slate-400">Instrument</span>
                    <span className="font-mono text-sm text-slate-200">{selectedSymbol.symbol}</span>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-navy-700/50 rounded-lg">
                    <span className="text-sm text-slate-400">Direction</span>
                    <span className={`text-sm font-semibold ${spotSide === 'buy' ? 'text-positive' : 'text-negative'}`}>
                      {spotSide.toUpperCase()}
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-navy-700/50 rounded-lg">
                    <span className="text-sm text-slate-400">Price</span>
                    <span className="font-mono text-sm text-slate-200">{formatINR(spotPrice)}</span>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-navy-700/50 rounded-lg">
                    <span className="text-sm text-slate-400">Quantity</span>
                    <span className="font-mono text-sm text-slate-200">{spotQuantity} share{spotQuantity > 1 ? 's' : ''}</span>
                  </div>

                  <div className="p-3 bg-navy-700/50 rounded-lg border border-navy-600">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-400">Estimated Value</span>
                      <span className="font-mono text-lg font-semibold text-slate-200">{formatINR(spotPrice * spotQuantity)}</span>
                    </div>
                  </div>
                </div>

                {orderError && (
                  <div className="mt-4 p-3 bg-negative/10 border border-negative/30 rounded-lg text-sm text-negative">
                    {orderError}
                  </div>
                )}

                <div className="flex items-center gap-3 mt-6">
                  <button
                    onClick={() => setShowOrderModal(false)}
                    className="flex-1 py-3 rounded-xl text-sm font-medium text-slate-400 hover:text-slate-200 bg-navy-700 hover:bg-navy-600 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handlePlaceSpotOrder}
                    disabled={orderLoading}
                    className={`flex-1 py-3 rounded-xl text-sm font-semibold transition-colors ${
                      spotSide === 'buy'
                        ? 'bg-positive hover:bg-positive/80 text-navy-900'
                        : 'bg-negative hover:bg-negative/80 text-white'
                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                    {orderLoading ? (
                      <svg className="w-5 h-5 animate-spin mx-auto" viewBox="0 0 24 24" fill="none">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeDasharray="32" strokeLinecap="round" />
                      </svg>
                    ) : (
                      `${spotSide === 'buy' ? 'BUY' : 'SELL'} ${spotQuantity} Share${spotQuantity > 1 ? 's' : ''}`
                    )}
                  </button>
                </div>
              </>
            ) : (
              <>
                {/* Options order details */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-navy-700/50 rounded-lg">
                    <span className="text-sm text-slate-400">Instrument</span>
                    <span className="font-mono text-sm text-slate-200">
                      {selectedSymbol.symbol} {selectedStrike.strike} {orderSide?.includes('CALL') ? 'CE' : 'PE'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-navy-700/50 rounded-lg">
                    <span className="text-sm text-slate-400">Direction</span>
                    <span className={`text-sm font-semibold ${orderSide?.startsWith('BUY') ? 'text-positive' : 'text-negative'}`}>
                      {orderSide?.startsWith('BUY') ? 'BUY' : 'SELL'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-navy-700/50 rounded-lg">
                    <span className="text-sm text-slate-400">Premium</span>
                    <span className="font-mono text-sm text-slate-200">
                      {formatINR(
                        (orderSide?.includes('CALL') ? selectedStrike.call?.ltp : selectedStrike.put?.ltp) || 0
                      )}
                    </span>
                  </div>

                  {/* Order type */}
                  <div>
                    <label className="text-xs text-slate-500 mb-2 block">Order Type</label>
                    <div className="flex gap-2">
                      {['MARKET', 'LIMIT'].map((type) => (
                        <button
                          key={type}
                          onClick={() => setOrderType(type)}
                          className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                            orderType === type
                              ? 'bg-accent text-navy-900'
                              : 'bg-navy-700 text-slate-400 hover:bg-navy-600'
                          }`}
                        >
                          {type}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Quantity */}
                  <div>
                    <label className="text-xs text-slate-500 mb-2 block">Quantity (Lots)</label>
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => setQuantity(Math.max(1, quantity - 1))}
                        className="w-10 h-10 rounded-lg bg-navy-700 text-slate-300 hover:bg-navy-600 flex items-center justify-center"
                      >
                        -
                      </button>
                      <input
                        type="number"
                        value={quantity}
                        onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                        className="flex-1 bg-navy-700 border border-navy-600 rounded-lg px-4 py-2 text-center font-mono text-slate-200 outline-none focus:border-accent/50"
                        min="1"
                      />
                      <button
                        onClick={() => setQuantity(quantity + 1)}
                        className="w-10 h-10 rounded-lg bg-navy-700 text-slate-300 hover:bg-navy-600 flex items-center justify-center"
                      >
                        +
                      </button>
                    </div>
                    <div className="text-xs text-slate-500 mt-1 text-right">
                      {quantity * (selectedSymbol.lot_size || 1)} shares ({quantity} lot{quantity > 1 ? 's' : ''} x {selectedSymbol.lot_size || 1})
                    </div>
                  </div>

                  {/* Estimated value */}
                  <div className="p-3 bg-navy-700/50 rounded-lg border border-navy-600">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-400">Estimated Value</span>
                      <span className="font-mono text-lg font-semibold text-slate-200">
                        {formatINR(
                          ((orderSide?.includes('CALL') ? selectedStrike.call?.ltp : selectedStrike.put?.ltp) || 0) *
                          quantity * (selectedSymbol.lot_size || 1)
                        )}
                      </span>
                    </div>
                  </div>
                </div>

                {orderError && (
                  <div className="mt-4 p-3 bg-negative/10 border border-negative/30 rounded-lg text-sm text-negative">
                    {orderError}
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center gap-3 mt-6">
                  <button
                    onClick={() => setShowOrderModal(false)}
                    className="flex-1 py-3 rounded-xl text-sm font-medium text-slate-400 hover:text-slate-200 bg-navy-700 hover:bg-navy-600 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handlePlaceOrder}
                    disabled={orderLoading}
                    className={`flex-1 py-3 rounded-xl text-sm font-semibold transition-colors ${
                      orderSide?.startsWith('BUY')
                        ? 'bg-positive hover:bg-positive/80 text-navy-900'
                        : 'bg-negative hover:bg-negative/80 text-white'
                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                    {orderLoading ? (
                      <svg className="w-5 h-5 animate-spin mx-auto" viewBox="0 0 24 24" fill="none">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeDasharray="32" strokeLinecap="round" />
                      </svg>
                    ) : (
                      `${orderSide?.startsWith('BUY') ? 'BUY' : 'SELL'} ${quantity} Lot${quantity > 1 ? 's' : ''}`
                    )}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
