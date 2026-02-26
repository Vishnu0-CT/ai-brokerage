import { get, post, del, put } from './client'

export const createConversation = (title) =>
  post('/api/conversations', { title })

export const listConversations = () => get('/api/conversations')

export const getConversation = (id) => get(`/api/conversations/${id}`)

export const updateConversation = (id, title) =>
  put(`/api/conversations/${id}`, { title })

export const deleteConversation = (id) => del(`/api/conversations/${id}`)

export const saveMessage = (conversationId, message) =>
  post(`/api/conversations/${conversationId}/messages`, message)

export const getMessages = (conversationId, limit = 50, offset = 0) =>
  get(`/api/conversations/${conversationId}/messages?limit=${limit}&offset=${offset}`)
