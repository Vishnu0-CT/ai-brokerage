import { get } from './client'

export const getPrice = (symbol) => get(`/api/market/price/${encodeURIComponent(symbol)}`)

export const getQuote = (symbol) => get(`/api/market/quote/${encodeURIComponent(symbol)}`)

export const getMarketHistory = (symbol, period = '1m') =>
  get(`/api/market/history/${encodeURIComponent(symbol)}?period=${period}`)
