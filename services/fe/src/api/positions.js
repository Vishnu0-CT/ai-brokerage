import { get, post } from './client'

export const getPositions = () => get('/api/positions')

export const getPositionsSummary = () => get('/api/positions/summary')

export const getPosition = (id) => get(`/api/positions/${id}`)

export const createPosition = (body) => post('/api/positions', body)

export const exitPosition = (id, body) => post(`/api/positions/${id}/exit`, body)

export const exitAllPositions = () => post('/api/positions/exit-all')
