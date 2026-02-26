import { get } from './client'

export const getOptionChain = (symbol, expiry) => {
  const qs = expiry ? `?expiry=${expiry}` : ''
  return get(`/api/option-chain/${encodeURIComponent(symbol)}${qs}`)
}

export const getExpiries = (weeks) => {
  const qs = weeks ? `?weeks=${weeks}` : ''
  return get(`/api/expiries${qs}`)
}
