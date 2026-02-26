import { get } from './client'

export const getMe = () => get('/api/user/me')
