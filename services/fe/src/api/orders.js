import { get, post, del } from './client'

export const getOrders = (params) => {
  const qs = new URLSearchParams()
  if (params?.symbol) qs.set('symbol', params.symbol)
  if (params?.side) qs.set('side', params.side)
  const q = qs.toString()
  return get(`/api/orders${q ? `?${q}` : ''}`)
}

export const placeOrder = (body) => post('/api/orders', body)

export const getConditions = () => get('/api/orders/conditions')

export const createCondition = (body) => post('/api/orders/conditions', body)

export const deleteCondition = (id) => del(`/api/orders/conditions/${id}`)
