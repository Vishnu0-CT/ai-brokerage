import { get } from './client'

export const getTradeHistory = (params) => {
  const qs = new URLSearchParams()
  if (params?.days) qs.set('days', params.days)
  if (params?.strategy) qs.set('strategy', params.strategy)
  if (params?.instrument) qs.set('instrument', params.instrument)
  const q = qs.toString()
  return get(`/api/trades${q ? `?${q}` : ''}`)
}

export const getTradeAnalytics = (days) => {
  const qs = days ? `?days=${days}` : ''
  return get(`/api/trades/analytics${qs}`)
}

export const getWeeklyPnl = (weeks) => {
  const qs = weeks ? `?weeks=${weeks}` : ''
  return get(`/api/trades/weekly-pnl${qs}`)
}

export const detectRevengeTrades = (lookback) => {
  const qs = lookback ? `?lookback=${lookback}` : ''
  return get(`/api/trades/detect/revenge${qs}`)
}

export const detectOvertrading = (threshold) => {
  const qs = threshold ? `?threshold=${threshold}` : ''
  return get(`/api/trades/detect/overtrading${qs}`)
}

export const getTradeSummary = () => get('/api/trades/summary')
