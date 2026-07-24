import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { User, Phone, Mail, Lock } from 'lucide-react'
import ModalShell from './ModalShell'
import { useUIStore } from '../../store/uiStore'
import { useAuthStore } from '../../store/authStore'
import { register } from '../../api/auth'
import PasswordStrengthIndicator, { isPasswordStrong } from './PasswordStrengthIndicator'
import { toTitleCase, formatTzPhone, isCompleteTzPhone } from '../../utils/formInput'

export default function BuyerSignupModal() {
  const { closeModal, openLogin } = useUIStore()
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    name: '',
    phone: '+255',
    email: '',
    password: '',
    password_confirmation: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  // The full name is usually two or three words (first/middle/last) —
  // capitalize each one live as the buyer types.
  const updateName = (field) => (e) => setForm({ ...form, [field]: toTitleCase(e.target.value) })

  const handlePhoneChange = (e) => {
    setForm({ ...form, phone: formatTzPhone(e.target.value) })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!form.name || !form.email || !form.password) {
      setError('Please fill in all fields')
      return
    }
    if (form.phone !== '+255' && !isCompleteTzPhone(form.phone)) {
      setError('Phone number must be +255 followed by exactly 9 digits')
      return
    }
    if (form.password !== form.password_confirmation) {
      setError('Passwords do not match')
      return
    }
    if (!isPasswordStrong(form.password)) {
      setError('Password must contain letters, numbers, and a special character')
      return
    }

    setLoading(true)
    try {
      const { data } = await register({
        name: form.name,
        email: form.email,
        password: form.password,
        password_confirmation: form.password_confirmation,
        role: 'buyer',
        phone: form.phone === '+255' ? null : form.phone,
      })
      setAuth(data.user, data.token)
      closeModal()
      toast.success(`Welcome to SmartFish, ${data.user.name}!`)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.message || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <ModalShell onClose={closeModal}>
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-blue-900">Create Buyer Account</h2>
        <p className="text-gray-500 mt-1">Browse sellers and order fresh fish</p>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 text-sm rounded-lg px-4 py-2 mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-3">
        <Field icon={User} placeholder="Full Name" value={form.name} onChange={updateName('name')} />
        <Field
          icon={Phone}
          placeholder="+255 7XX XXX XXX"
          value={form.phone}
          onChange={handlePhoneChange}
        />
        <Field
          icon={Mail}
          type="email"
          placeholder="Email"
          value={form.email}
          onChange={update('email')}
        />
        <Field
          icon={Lock}
          type="password"
          placeholder="Password"
          value={form.password}
          onChange={update('password')}
        />
        <PasswordStrengthIndicator password={form.password} />
        <Field
          icon={Lock}
          type="password"
          placeholder="Confirm Password"
          value={form.password_confirmation}
          onChange={update('password_confirmation')}
        />

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-700 hover:bg-blue-800 text-white font-semibold py-3 rounded-lg transition mt-2 disabled:opacity-50"
        >
          {loading ? 'Creating account…' : 'Create Account'}
        </button>
      </form>

      <p className="text-center text-sm text-gray-500 mt-5">
        Already have an account?{' '}
        <button onClick={openLogin} className="text-blue-700 font-semibold hover:underline">
          Log in
        </button>
      </p>
    </ModalShell>
  )
}

function Field({ icon: Icon, type = 'text', placeholder, value, onChange }) {
  return (
    <div className="flex items-center border border-gray-300 rounded-lg px-3 py-2.5 focus-within:ring-2 focus-within:ring-blue-400">
      <Icon className="w-4 h-4 text-blue-600 mr-3 flex-shrink-0" />
      <input
        type={type}
        required
        placeholder={placeholder}
        className="w-full outline-none text-sm"
        value={value}
        onChange={onChange}
      />
    </div>
  )
}
