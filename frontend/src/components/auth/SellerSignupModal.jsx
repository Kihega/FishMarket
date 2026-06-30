import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { User, Store, MapPin, Mail, Phone, Lock } from 'lucide-react'
import ModalShell from './ModalShell'
import { useUIStore } from '../../store/uiStore'
import { useAuthStore } from '../../store/authStore'
import { register } from '../../api/auth'
import PasswordStrengthIndicator, { isPasswordStrong } from './PasswordStrengthIndicator'
import { toTitleCase, formatTzPhone, isCompleteTzPhone } from '../../utils/formInput'

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
  const [logo, setLogo] = useState(null)
  const [logoPreview, setLogoPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  // Names are typically two or three words (first/middle/last) — each
  // word is capitalized live as the seller types, so the form already
  // shows "John Peter Mwasege" instead of relying on the backend to
  // fix it after submit.
  const updateName = (field) => (e) => setForm({ ...form, [field]: toTitleCase(e.target.value) })

  const handlePhoneChange = (e) => {
    setForm({ ...form, phone: formatTzPhone(e.target.value) })
  }

  const handleLogoChange = (e) => {
    const file = e.target.files[0]
    setLogo(file)
    setLogoPreview(file ? URL.createObjectURL(file) : null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!form.name || !form.business_name || !form.location || !form.email || !form.password) {
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
      // No subscription/plan step — this is a research/testing build,
      // not a live payment system. Sellers are immediately active.
      // Brand logo is collected here, during account creation, instead
      // of as a separate step inside the seller dashboard.
      const fd = new FormData()
      fd.append('name', form.name)
      fd.append('business_name', form.business_name)
      fd.append('email', form.email)
      fd.append('password', form.password)
      fd.append('password_confirmation', form.password_confirmation)
      fd.append('role', 'seller')
      if (form.phone !== '+255') fd.append('phone', form.phone)
      fd.append('location', form.location)
      fd.append('office_address', form.location)
      if (logo) fd.append('brand_logo', logo)

      const { data } = await register(fd)

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
        <Field icon={User} placeholder="Full Name" value={form.name} onChange={updateName('name')} />
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

        {/* Business Brand Logo — moved here from the seller dashboard Home
            panel, as part of account creation. Optional. */}
        <div>
          <label className="block text-sm text-gray-500 mb-1">Business Brand Logo (optional)</label>
          <div className="flex items-center gap-3">
            <div className="w-14 h-14 rounded-full border-2 border-dashed border-gray-300 flex items-center justify-center overflow-hidden bg-gray-50 flex-shrink-0">
              {logoPreview ? (
                <img src={logoPreview} alt="Logo preview" className="w-full h-full object-cover" />
              ) : (
                <Store className="w-5 h-5 text-gray-300" />
              )}
            </div>
            <input
              className="input flex-1 text-sm" type="file" accept="image/*"
              onChange={handleLogoChange}
            />
          </div>
        </div>

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
