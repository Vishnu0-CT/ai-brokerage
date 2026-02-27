import { useState, useEffect, useMemo } from 'react'
import { useApi } from '../../hooks/useApi'
import { useWatchlistPriceStream } from '../../hooks/useWatchlistPriceStream'
import { getBalance } from '../../api/portfolio'
import { getHoldings } from '../../api/portfolio'
import { getWatchlist } from '../../api/watchlist'
import { formatINR, getPnlColor } from '../../utils/formatters'

function MarketTicker({ data }) {
  if (!data) return null
  const isPositive = (data.change_percent || 0) >= 0

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-navy-700/50">
      <span className="text-slate-400 text-xs font-medium">{data.symbol}</span>
      <span className="font-mono text-sm font-semibold text-slate-100">
        {(data.price || 0).toLocaleString('en-IN')}
      </span>
      <span className={`font-mono text-xs ${isPositive ? 'text-positive' : 'text-negative'}`}>
        {isPositive ? '+' : ''}{(data.change_percent || 0).toFixed(2)}%
      </span>
    </div>
  )
}

function LiveClock() {
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="font-mono text-sm text-slate-300">
      {time.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      })}
    </div>
  )
}

export default function Header() {
  const { data: balance } = useApi(() => getBalance(), [])
  const { data: positions } = useApi(() => getHoldings(), [])
  const { data: watchlist } = useApi(() => getWatchlist(), [])
  const { priceUpdates } = useWatchlistPriceStream(true)

  // Merge watchlist with real-time prices
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
        }
      }
      return item
    })
  }, [watchlist, priceUpdates])

  // Calculate real-time P&L
  const realTimePnl = useMemo(() => {
    if (!balance || !positions || Object.keys(priceUpdates).length === 0) {
      return balance?.total_pnl || 0
    }

    // Calculate total unrealized P&L from positions with real-time prices
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
  }, [balance, positions, priceUpdates])

  const pnlColor = getPnlColor(realTimePnl)

  // Extract index tickers from watchlist (NIFTY, BANKNIFTY, VIX)
  const nifty = watchlistWithPrices?.find(w => w.symbol === 'NIFTY' || w.symbol === 'NIFTY 50')
  const bankNifty = watchlistWithPrices?.find(w => w.symbol === 'BANKNIFTY' || w.symbol === 'BANK NIFTY')
  const vix = watchlistWithPrices?.find(w => w.symbol === 'INDIA VIX' || w.symbol === 'VIX')

  return (
    <header className="h-16 bg-navy-800 border-b border-navy-600 px-6 flex items-center justify-between sticky top-0 z-50">
      {/* Logo */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center">
          <svg className="w-5 h-5 text-navy-900" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M3 17l6-6 4 4 8-8" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="21" cy="7" r="2" fill="currentColor" />
          </svg>
        </div>
        <span className="text-lg font-semibold text-white tracking-tight">
          Clear<span className="text-accent">Trade</span>
        </span>
      </div>

      {/* Market Tickers */}
      <div className="hidden md:flex items-center gap-3">
        <MarketTicker data={nifty} />
        <MarketTicker data={bankNifty} />
        <MarketTicker data={vix} />
      </div>

      {/* Right side - Clock and P&L */}
      <div className="flex items-center gap-6">
        <LiveClock />

        <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-navy-700/50 border border-navy-600">
          <span className="text-xs text-slate-400">Today's P&L</span>
          <span className={`font-mono text-sm font-semibold ${pnlColor}`}>
            {formatINR(realTimePnl, true)}
          </span>
        </div>

        {/* Live indicator */}
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-positive pulse-live" />
          <span className="text-xs text-slate-400">LIVE</span>
        </div>
      </div>
    </header>
  )
}
