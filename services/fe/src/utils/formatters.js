/**
 * Format a number as Indian Rupees
 */
export function formatINR(value, showSign = false) {
  const absValue = Math.abs(value)
  const sign = value >= 0 ? (showSign ? '+' : '') : '-'

  const formatted = absValue.toLocaleString('en-IN', {
    maximumFractionDigits: 0,
  })

  return `${sign}₹${formatted}`
}

/**
 * Format a number in lakhs/crores
 */
export function formatLakhsCrores(value) {
  const absValue = Math.abs(value)
  const sign = value >= 0 ? '' : '-'

  if (absValue >= 10000000) {
    return `${sign}₹${(absValue / 10000000).toFixed(2)}Cr`
  } else if (absValue >= 100000) {
    return `${sign}₹${(absValue / 100000).toFixed(2)}L`
  } else if (absValue >= 1000) {
    return `${sign}₹${(absValue / 1000).toFixed(1)}K`
  }
  return `${sign}₹${absValue}`
}

/**
 * Format percentage
 */
export function formatPercent(value, showSign = false) {
  const sign = value >= 0 ? (showSign ? '+' : '') : ''
  return `${sign}${value.toFixed(2)}%`
}

/**
 * Get color class based on value (positive/negative)
 */
export function getPnlColor(value) {
  if (value > 0) return 'text-positive'
  if (value < 0) return 'text-negative'
  return 'text-slate-400'
}

/**
 * Get background color class based on value
 */
export function getPnlBgColor(value) {
  if (value > 0) return 'bg-positive/10'
  if (value < 0) return 'bg-negative/10'
  return 'bg-slate-500/10'
}

/**
 * Format time for display
 */
export function formatTime(date) {
  const d = new Date(date)
  return d.toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

/**
 * Format date for display
 */
export function formatDate(date) {
  const d = new Date(date)
  return d.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
  })
}

/**
 * Format timestamp for chat messages
 */
export function formatTimestamp(date) {
  const d = new Date(date)
  return d.toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  })
}

/**
 * Format number with Indian comma separators
 */
export function formatNumber(value) {
  return value.toLocaleString('en-IN')
}

/**
 * Get severity color for alerts
 */
export function getSeverityColors(severity) {
  switch (severity) {
    case 'critical':
      return { text: 'text-negative', bg: 'bg-negative/20', border: 'border-negative/50' }
    case 'high':
      return { text: 'text-negative', bg: 'bg-negative/10', border: 'border-negative/30' }
    case 'medium':
      return { text: 'text-warning', bg: 'bg-warning/10', border: 'border-warning/30' }
    case 'low':
      return { text: 'text-accent', bg: 'bg-accent/10', border: 'border-accent/30' }
    default:
      return { text: 'text-slate-400', bg: 'bg-slate-500/10', border: 'border-slate-500/30' }
  }
}

/**
 * Calculate time ago string
 */
export function timeAgo(date) {
  const now = new Date()
  const d = new Date(date)
  const diffMs = now - d
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  return formatDate(date)
}
