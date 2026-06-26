import { useState } from 'react'
import toast from 'react-hot-toast'
import client from '../../api/client'
import ModalShell from '../auth/ModalShell'
import PasswordStrengthIndicator, { isPasswordStrong } from '../auth/PasswordStrengthIndicator'

export default function ChangePasswordModal({ onClose }) {
  const [form, setForm] = useState({
    current_password: '',
    password: '',
    password_confirmation: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (form.password !== form.password_confirmation) {
      setError('New passwords do not match')
      return
    }
    if (!isPasswordStrong(form.password)) {
      setError('Password must contain letters, numbers, and a special character')
      return
    }

    setLoading(true)
    try {
      await client.put('/password', form)
      toast.success('Password updated successfully')
      onClose()
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to update password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <ModalShell onClose={onClose}>
      <h2 className="text-xl font-bold text-blue-900 mb-4">Change Password</h2>

      {error && (
        <div className="bg-red-50 text-red-600 text-sm rounded-lg px-4 py-2 mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          type="password"
          required
          placeholder="Current Password"
          className="input"
          value={form.current_password}
          onChange={(e) => setForm({ ...form, current_password: e.target.value })}
        />
        <input
          type="password"
          required
          placeholder="New Password"
          className="input"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />
        <PasswordStrengthIndicator password={form.password} />
        <input
          type="password"
          required
          placeholder="Confirm New Password"
          className="input"
          value={form.password_confirmation}
          onChange={(e) => setForm({ ...form, password_confirmation: e.target.value })}
        />
        <button type="submit" disabled={loading} className="btn-primary w-full">
          {loading ? 'Updating…' : 'Update Password'}
        </button>
      </form>
    </ModalShell>
  )
}
