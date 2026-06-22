import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import ModalShell from './ModalShell'
import { useUIStore } from '../../store/uiStore'
import { useAuthStore } from '../../store/authStore'
import { login } from '../../api/auth'

export default function LoginModal() {
  const { closeModal, openSignupChoice } = useUIStore()
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await login(form)
      setAuth(data.user, data.token)
      closeModal()
      navigate(data.user.role === 'admin' ? '/admin' : '/dashboard')
      toast.success(`Welcome back, ${data.user.name}!`)
    } catch (err) {
      setError(err.response?.data?.message || 'Invalid email or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <ModalShell onClose={closeModal}>
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-blue-900">🐟 FishMarket TZ</h2>
        <p className="text-gray-500 mt-1">Log in to your account</p>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 text-sm rounded-lg px-4 py-2 mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex items-center border border-gray-300 rounded-lg px-3 py-2.5 focus-within:ring-2 focus-within:ring-blue-400">
          <i className="fas fa-envelope text-blue-600 mr-3" />
          <input
            type="email"
            required
            placeholder="Email"
            className="w-full outline-none"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
        </div>

        <div className="flex items-center border border-gray-300 rounded-lg px-3 py-2.5 focus-within:ring-2 focus-within:ring-blue-400">
          <i className="fas fa-lock text-blue-600 mr-3" />
          <input
            type="password"
            required
            placeholder="Password"
            className="w-full outline-none"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-700 hover:bg-blue-800 text-white font-semibold py-3 rounded-lg transition disabled:opacity-50"
        >
          {loading ? 'Logging in…' : 'Login'}
        </button>
      </form>

      <p className="text-center text-sm text-gray-500 mt-5">
        Don't have an account?{' '}
        <button
          onClick={openSignupChoice}
          className="text-blue-700 font-semibold hover:underline"
        >
          Sign up
        </button>
      </p>
    </ModalShell>
  )
}
