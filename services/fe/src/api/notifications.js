import { get, post, patch, del } from './client'

export async function getNotifications(unreadOnly = false) {
  const params = unreadOnly ? '?unread_only=true' : ''
  return await get(`/api/notifications${params}`)
}

export async function getUnreadCount() {
  return await get('/api/notifications/unread-count')
}

export async function createNotification(data) {
  return await post('/api/notifications', data)
}

export async function updateNotification(id, data) {
  return await patch(`/api/notifications/${id}`, data)
}

export async function markAllRead() {
  return await post('/api/notifications/mark-all-read')
}

export async function deleteNotification(id) {
  return await del(`/api/notifications/${id}`)
}
