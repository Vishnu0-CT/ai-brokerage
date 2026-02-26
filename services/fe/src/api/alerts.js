import { get, patch } from './client'

export const getAlerts = () => get('/api/alerts')

export const getRiskMetrics = () => get('/api/alerts/risk-metrics')

export const dismissAlert = (id) => patch(`/api/alerts/${id}/dismiss`)
