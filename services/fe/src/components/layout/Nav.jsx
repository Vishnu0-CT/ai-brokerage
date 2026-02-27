import { NavLink } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { getUnreadCount } from '../../api/notifications'

const navItems = [
  {
    path: '/dashboard',
    label: 'Dashboard',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </svg>
    ),
  },
  {
    path: '/trade',
    label: 'Trade',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M3 17l6-6 4 4 8-8" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M17 7h4v4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    path: '/strategy',
    label: 'Strategy Builder',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    highlight: true,
    badge: 'NEW',
  },
  {
    path: '/risk',
    label: 'Risk Monitor',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 9v4M12 17h.01" strokeLinecap="round" />
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      </svg>
    ),
  },
  {
    path: '/coach',
    label: 'Performance Coach',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M3 3v18h18" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M7 16l4-4 4 4 6-6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
]

export default function Nav({ onNotificationClick }) {
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    loadUnreadCount()
    // Poll for updates every 30 seconds
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

  return (
    <nav className="w-56 bg-navy-800 border-r border-navy-600 flex flex-col py-4">
      <div className="flex-1 px-3 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group ${
                isActive
                  ? 'bg-navy-700 text-accent border-l-2 border-accent -ml-[2px] pl-[18px]'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-navy-700/50'
              } ${item.highlight && !isActive ? 'ring-1 ring-accent/30' : ''}`
            }
          >
            <span className="group-hover:scale-110 transition-transform">
              {item.icon}
            </span>
            <span className="font-medium text-sm">{item.label}</span>
            {item.badge ? (
              <span className="ml-auto px-1.5 py-0.5 text-[10px] font-semibold bg-positive/20 text-positive rounded">
                {item.badge}
              </span>
            ) : item.highlight ? (
              <span className="ml-auto px-1.5 py-0.5 text-[10px] font-semibold bg-accent/20 text-accent rounded">
                AI
              </span>
            ) : null}
          </NavLink>
        ))}
      </div>

      {/* Bottom section */}
      <div className="px-3 pt-4 border-t border-navy-600 mt-4 space-y-2">
        {/* Notifications button */}
        <button
          onClick={onNotificationClick}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-navy-700/50 transition-all duration-200 group relative"
        >
          <span className="group-hover:scale-110 transition-transform">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
          <span className="font-medium text-sm">Notifications</span>
          {unreadCount > 0 && (
            <span className="ml-auto w-5 h-5 flex items-center justify-center text-[10px] font-bold bg-accent text-navy-900 rounded-full">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>

        <div className="px-4 py-3 rounded-lg bg-navy-700/30">
          <div className="text-xs text-slate-500 mb-1">Account</div>
          <div className="text-sm font-medium text-slate-300">ClearTrade</div>
          <div className="text-xs text-accent mt-1">● Live</div>
        </div>
      </div>
    </nav>
  )
}
