import { get, post, put, del } from './client'

export const listStrategies = (status) => {
  const qs = status ? `?status=${status}` : ''
  return get(`/api/strategies${qs}`)
}

export const createStrategy = (body) => post('/api/strategies', body)

export const getStrategy = (id) => get(`/api/strategies/${id}`)

export const updateStrategy = (id, body) => put(`/api/strategies/${id}`, body)

export const deleteStrategy = (id) => del(`/api/strategies/${id}`)

export const parseStrategy = (description) =>
  post('/api/strategies/parse', { description })

export const getTemplates = () => get('/api/strategies/templates')

export const getTemplateCategories = () => get('/api/strategies/templates/categories')

export const getTemplate = (id) => get(`/api/strategies/templates/${id}`)

export const getStrategyVersions = (id) => get(`/api/strategies/${id}/versions`)
