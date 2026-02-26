import { get, post } from './client'

export const getCoaching = (period = '1m') =>
  get(`/api/analytics/coaching?period=${period}`)

export const getWinRateByTime = (period = '1m') =>
  get(`/api/analytics/win-rate-by-time?period=${period}`)

export const getInstrumentStats = (period = '1m') =>
  get(`/api/analytics/instrument-stats?period=${period}`)

export const getTrades = (params) => {
  const qs = new URLSearchParams()
  if (params?.instrument) qs.set('instrument', params.instrument)
  if (params?.direction) qs.set('direction', params.direction)
  if (params?.date_range_start) qs.set('date_range_start', params.date_range_start)
  if (params?.date_range_end) qs.set('date_range_end', params.date_range_end)
  const q = qs.toString()
  return get(`/api/analytics/trades${q ? `?${q}` : ''}`)
}

export const getMetrics = (params) => {
  const qs = new URLSearchParams()
  if (params?.metric) qs.set('metric', params.metric)
  if (params?.group_by) qs.set('group_by', params.group_by)
  if (params?.instrument) qs.set('instrument', params.instrument)
  const q = qs.toString()
  return get(`/api/analytics/metrics${q ? `?${q}` : ''}`)
}

export const getExposure = (by = 'instrument') =>
  get(`/api/analytics/exposure?by=${by}`)

export const simulate = (body) => post('/api/analytics/simulate', body)

export const getTradePatterns = (params) => {
  const qs = new URLSearchParams()
  if (params?.event_type) qs.set('event_type', params.event_type)
  if (params?.lookback_count) qs.set('lookback_count', params.lookback_count)
  if (params?.min_loss_amount) qs.set('min_loss_amount', params.min_loss_amount)
  const q = qs.toString()
  return get(`/api/analytics/trade-patterns${q ? `?${q}` : ''}`)
}

export const getTradingSignal = () => get('/api/analytics/trading-signal')
