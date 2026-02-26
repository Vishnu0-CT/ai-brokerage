import { get, post, del } from './client'

export const getWatchlist = () => get('/api/watchlist')

export const addToWatchlist = (body) => post('/api/watchlist', body)

export const removeFromWatchlist = (id) => del(`/api/watchlist/${id}`)

export const seedWatchlist = () => post('/api/watchlist/seed')
