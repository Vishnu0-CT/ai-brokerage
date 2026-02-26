import { BE_BASE_URL } from '../config'

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.status = status
    this.data = data
  }
}

async function request(path, options = {}) {
  const url = `${BE_BASE_URL}${path}`
  const config = {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  }

  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body)
  }

  const res = await fetch(url, config)

  if (!res.ok) {
    let data
    try { data = await res.json() } catch { data = null }
    
    // Handle FastAPI validation errors (detail is an array)
    let message = `Request failed (${res.status})`
    if (data?.detail) {
      if (Array.isArray(data.detail)) {
        // FastAPI validation errors: [{loc: [...], msg: "...", type: "..."}]
        message = data.detail.map(err => {
          const field = err.loc?.slice(-1)[0] || 'field'
          return `${field}: ${err.msg}`
        }).join('; ')
      } else if (typeof data.detail === 'string') {
        message = data.detail
      }
    } else if (data?.message) {
      message = data.message
    }
    
    throw new ApiError(message, res.status, data)
  }

  if (res.status === 204) return null
  return res.json()
}

export const get = (path) => request(path)
export const post = (path, body) => request(path, { method: 'POST', body })
export const put = (path, body) => request(path, { method: 'PUT', body })
export const patch = (path, body) => request(path, { method: 'PATCH', body })
export const del = (path) => request(path, { method: 'DELETE' })
