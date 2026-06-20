import client from './client'

export const register = (data) => client.post('/register', data)
export const login = (data) => client.post('/login', data)
export const logout = () => client.post('/logout')
export const getMe = () => client.get('/me')
