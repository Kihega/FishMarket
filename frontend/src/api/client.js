import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
  // Generous timeout for Render cold-starts on production
  timeout: 45000,
})

client.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

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

/**
 * Resolve an image value from the backend.
 *
 * The backend stores either:
 *   - "data:image/...;base64,..."  (local mode)
 *   - "https://..."                (production full URL)
 *
 * Returns null for falsy input so callers can safely do:
 *   {resolveImage(src) && <img src={resolveImage(src)} />}
 */
export function resolveImage(src) {
  if (!src) return null
  if (src.startsWith('data:') || src.startsWith('http')) return src
  // Fallback for old disk-path values (e.g. "stocks/abc.jpg")
  const base = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/api\/?$/, '')
  return `${base}/storage/${src}`
}
