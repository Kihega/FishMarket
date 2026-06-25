import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { User, Store, MapPin, Mail, Phone, Lock } from 'lucide-react'
import ModalShell from './ModalShell'
import { useUIStore } from '../../store/uiStore'
import { useAuthStore } from '../../store/authStore'
import { register } from '../../api/auth'
import PasswordStrengthIndicator, { isPasswordStrong } from './PasswordStrengthIndicator'

export default function SellerSignupModal() {
  const { closeModal, openLogin } = useUIStore()
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    name: '',
    business_name: '',
    location: '',
    email: '',
    phone: '+255',
    password: '',
    password_confirmation: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const handlePhoneChange = (e) => {
    let val = e.target.value
    if (!val.startsWith('+255')) val = '+255'
    setForm({ ...form, phone: val })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!form.name || !form.business_name || !form.location || !form.email || !form.password) {
      setError('Please fill in all fields')
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
      // No subscription/plan step — this is a research/testing build,
      // not a live payment system. Sellers are immediately active.
      const { data } = await register({
        name: form.name,
        business_name: form.business_name,
        email: form.email,
        password: form.password,
        password_confirmation: form.password_confirmation,
        role: 'seller',
        phone: form.phone,
        location: form.location,
        office_address: form.location,
      })

      setAuth(data.user, data.token)
      closeModal()
      toast.success(`Welcome to SmartFish, ${data.user.business_name || data.user.name}!`)
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
        <h2 className="text-2xl font-bold text-blue-900">Create Seller Account</h2>
        <p className="text-gray-500 mt-1">Your business details</p>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 text-sm rounded-lg px-4 py-2 mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-3">
        <Field icon={User} placeholder="Full Name" value={form.name} onChange={update('name')} />
        <Field
          icon={Store}
          placeholder="Business / Brand Name"
          value={form.business_name}
          onChange={update('business_name')}
        />
        <Field
          icon={MapPin}
          placeholder="Physical Address / Location"
          value={form.location}
          onChange={update('location')}
        />
        <Field
          icon={Mail}
          type="email"
          placeholder="Email"
          value={form.email}
          onChange={update('email')}
        />
        <Field
          icon={Phone}
          placeholder="+255 7XX XXX XXX"
          value={form.phone}
          onChange={handlePhoneChange}
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
