import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
  // Render's free tier can take 30-50s to wake from sleep on the first
  // request. We give it generous room here rather than failing fast,
  // since a quick timeout would make cold starts look like real errors.
  timeout: 45000,
})

// Attach the Sanctum token to every outgoing request, if present.
client.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// If the backend ever returns 401 (expired/invalid token), clear local
// auth state so the UI falls back to logged-out behavior instead of
// silently failing every subsequent request.
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore.getState().clearAuth()
    }
    return Promise.reject(err)
  }
)

export default client
