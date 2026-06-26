import client from './client'

// `data` may be a plain object (JSON) or a FormData instance (used by the
// seller signup form, which can include an optional brand_logo file).
export const register = (data) =>
  client.post('/register', data, {
    headers: data instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : {},
  })
export const login = (data) => client.post('/login', data)
export const logout = () => client.post('/logout')
export const getMe = () => client.get('/me')
