import client from './client'

// `data` may be a plain object (JSON) or a FormData instance (used by the
// seller signup form, which can include an optional brand_logo file).
// Axios sets the correct multipart boundary automatically when it sees a
// FormData body — manually forcing 'multipart/form-data' here (with no
// boundary) produced a request body Laravel couldn't parse at all.
export const register = (data) => client.post('/register', data)
export const login = (data) => client.post('/login', data)
export const logout = () => client.post('/logout')
export const getMe = () => client.get('/me')
