import { useState, useEffect } from 'react'
import { useApi } from '../../hooks/useApi'
import { getBalance } from '../../api/portfolio'
import { getWatchlist } from '../../api/watchlist'
import { getUnreadCount } from '../../api/notifications'
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

export default function Header({ onToggleAssistant, isAssistantOpen = false, onNotificationClick }) {
  const { data: balance } = useApi(() => getBalance(), [])
  const { data: watchlist } = useApi(() => getWatchlist(), [])
  const [unreadCount, setUnreadCount] = useState(0)

  const pnl = balance?.total_pnl || 0
  const pnlColor = getPnlColor(pnl)

  useEffect(() => {
    loadUnreadCount()
    const interval = setInterval(loadUnreadCount, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadUnreadCount = async () => {
    try {
      const data = await getUnreadCount()
      setUnreadCount(data.count)
    } catch (error) {
      console.error('Failed to load unread count:', error)
    }
  }

  // Extract index tickers from watchlist (NIFTY, BANKNIFTY, VIX)
  const nifty = watchlist?.find(w => w.symbol === 'NIFTY 50')
  const bankNifty = watchlist?.find(w => w.symbol === 'BANKNIFTY' || w.symbol === 'BANK NIFTY')
  const vix = watchlist?.find(w => w.symbol === 'INDIA VIX')

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

      {/* Right side - Clock, P&L, and AI Assistant Button */}
      <div className="flex items-center gap-6">
        <LiveClock />

        <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-navy-700/50 border border-navy-600">
          <span className="text-xs text-slate-400">Today's P&L</span>
          <span className={`font-mono text-sm font-semibold ${pnlColor}`}>
            {formatINR(pnl, true)}
          </span>
        </div>

        {/* Notification Bell */}
        <button
          onClick={onNotificationClick}
          className="relative p-2 rounded-lg hover:bg-navy-700 text-slate-400 hover:text-slate-200 transition-colors"
        >
          <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 flex items-center justify-center text-[10px] font-bold bg-accent text-navy-900 rounded-full">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>

        {/* AI Assistant Button */}
        <button
          onClick={onToggleAssistant}
          className={`relative flex items-center gap-2.5 px-5 py-2.5 rounded-xl shadow-lg transition-all duration-300 group overflow-hidden ${
            isAssistantOpen
              ? 'bg-gradient-to-r from-accent-dark to-accent shadow-accent/40 scale-95'
              : 'bg-gradient-to-r from-accent to-accent-dark hover:from-accent-dark hover:to-accent shadow-accent/20 hover:shadow-accent/40'
          }`}
        >
          {/* Animated background glow */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
          
          <svg 
            className={`w-5 h-5 text-navy-900 transition-transform duration-500 ${
              isAssistantOpen ? 'rotate-180' : 'group-hover:rotate-180'
            }`} 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2.5"
          >
            <path d="M12 2a10 10 0 0 1 10 10c0 5.523-4.477 10-10 10a10 10 0 0 1-10-10A10 10 0 0 1 12 2z" />
            <circle cx="12" cy="12" r="3" fill="currentColor" />
            <path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
          </svg>
          <span className="text-sm font-bold text-navy-900 tracking-wide relative z-10">
            {isAssistantOpen ? 'Close Assistant' : 'AI Assistant'}
          </span>
          
          {/* Pulse indicator - only show when not open */}
          {!isAssistantOpen && (
            <>
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-positive rounded-full animate-ping" />
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-positive rounded-full" />
            </>
          )}
          
          {/* Active indicator - show when open */}
          {isAssistantOpen && (
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-navy-900 rounded-full border-2 border-accent" />
          )}
        </button>

        {/* Live indicator */}
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-positive pulse-live" />
          <span className="text-xs text-slate-400">LIVE</span>
        </div>
      </div>
    </header>
  )
}
