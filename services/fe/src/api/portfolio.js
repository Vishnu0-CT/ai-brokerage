import { get } from './client'

export const getHoldings = (params) => {
  const qs = new URLSearchParams()
  if (params?.instrument) qs.set('instrument', params.instrument)
  if (params?.filter) qs.set('filter', params.filter)
  const q = qs.toString()
  return get(`/api/portfolio/holdings${q ? `?${q}` : ''}`)
}

export const getBalance = () => get('/api/portfolio/balance')

export const getSummary = () => get('/api/portfolio/summary')

export const getHistory = (period = '1d') =>
  get(`/api/portfolio/history?period=${period}`)
