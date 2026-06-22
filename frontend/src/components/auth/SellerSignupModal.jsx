import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import ModalShell from './ModalShell'
import { useUIStore } from '../../store/uiStore'
import { useAuthStore } from '../../store/authStore'
import { register } from '../../api/auth'
import { createSubscription } from '../../api/subscriptions'

const PLANS = [
  {
    id: 'free',
    name: 'Free Tier',
    price: 'TZS 0',
    period: 'for now',
    tag: 'Recommended for testing',
    features: ['Up to 10 fish stock items', 'Basic seller dashboard', 'No card required'],
  },
  {
    id: 'monthly',
    name: 'Monthly',
    price: 'TZS 15,000',
    period: '/ month',
    features: ['Unlimited stock items', 'Priority listing', 'Sales analytics'],
  },
  {
    id: 'annual',
    name: 'Annually',
    price: 'TZS 150,000',
    period: '/ year',
    tag: 'Save 17%',
    features: ['Everything in Monthly', '2 months free', 'Dedicated support'],
  },
]

export default function SellerSignupModal() {
  const { closeModal, openLogin, sellerSignupStep, nextSellerStep, prevSellerStep } = useUIStore()
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
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const handlePhoneChange = (e) => {
    let val = e.target.value
    if (!val.startsWith('+255')) val = '+255'
    setForm({ ...form, phone: val })
  }

  const validateStep1 = () => {
    if (!form.name || !form.business_name || !form.location || !form.email || !form.password) {
      setError('Please fill in all fields')
      return false
    }
    if (form.password !== form.password_confirmation) {
      setError('Passwords do not match')
      return false
    }
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters')
      return false
    }
    return true
  }

  const handleContinue = (e) => {
    e.preventDefault()
    setError('')
    if (!validateStep1()) return
    nextSellerStep()
  }

  const handleSelectPlan = async (planId) => {
    setSelectedPlan(planId)
    setLoading(true)
    setError('')
    try {
      // 1. Register the seller account
      const { data } = await register({
        name: form.name,
        email: form.email,
        password: form.password,
        password_confirmation: form.password_confirmation,
        role: 'seller',
        phone: form.phone,
        location: form.location,
        office_address: form.location,
      })

      // 2. Record their chosen plan.
      //    Free tier => account is immediately usable, no payment step
      //    (this is a research/testing build, not a live payment system).
      if (planId !== 'free') {
        await createSubscription({ plan: planId }).catch(() => {
          // Non-fatal here — admin can still confirm manually later.
        })
      }

      setAuth(data.user, data.token)
      closeModal()
      toast.success(
        planId === 'free'
          ? 'Account created! You are on the Free Tier — welcome to your dashboard.'
          : 'Account created! Your plan is pending admin confirmation.'
      )
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.message || 'Something went wrong. Please try again.')
      setSelectedPlan(null)
    } finally {
      setLoading(false)
    }
  }

  // ── STEP 2: Plan picker ────────────────────────────────────────────
  if (sellerSignupStep === 2) {
    return (
      <ModalShell onClose={closeModal} maxWidth="max-w-2xl">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-blue-900">Choose Your Plan</h2>
          <p className="text-gray-500 mt-1">
            You can change this later from your dashboard
          </p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 text-sm rounded-lg px-4 py-2 mb-4 text-center">
            {error}
          </div>
        )}

        <div className="grid md:grid-cols-3 gap-4">
          {PLANS.map((plan) => (
            <div
              key={plan.id}
              className={`border-2 rounded-xl p-5 flex flex-col ${
                plan.id === 'free' ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
              }`}
            >
              {plan.tag && (
                <span className="text-xs font-semibold text-blue-700 bg-blue-100 rounded-full px-2 py-0.5 self-start mb-2">
                  {plan.tag}
                </span>
              )}
              <h3 className="font-bold text-blue-900">{plan.name}</h3>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {plan.price}
                <span className="text-sm font-normal text-gray-500"> {plan.period}</span>
              </p>
              <ul className="text-sm text-gray-600 mt-3 space-y-1 flex-1">
                {plan.features.map((f) => (
                  <li key={f} className="flex gap-2">
                    <span className="text-blue-600">✓</span> {f}
                  </li>
                ))}
              </ul>
              <button
                onClick={() => handleSelectPlan(plan.id)}
                disabled={loading}
                className={`mt-4 w-full py-2.5 rounded-lg font-semibold transition disabled:opacity-50 ${
                  plan.id === 'free'
                    ? 'bg-blue-700 text-white hover:bg-blue-800'
                    : 'border-2 border-blue-700 text-blue-700 hover:bg-blue-50'
                }`}
              >
                {loading && selectedPlan === plan.id ? 'Setting up…' : `Choose ${plan.name}`}
              </button>
            </div>
          ))}
        </div>

        <button
          onClick={prevSellerStep}
          className="text-sm text-gray-500 hover:underline mt-5 block mx-auto"
        >
          ← Back to details
        </button>
      </ModalShell>
    )
  }

  // ── STEP 1: Seller details ──────────────────────────────────────
  return (
    <ModalShell onClose={closeModal}>
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-blue-900">Create Seller Account</h2>
        <p className="text-gray-500 mt-1">Step 1 of 2 — Your business details</p>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 text-sm rounded-lg px-4 py-2 mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleContinue} className="space-y-3">
        <Field icon="fa-user" placeholder="Full Name" value={form.name} onChange={update('name')} />
        <Field
          icon="fa-store"
          placeholder="Business / Brand Name"
          value={form.business_name}
          onChange={update('business_name')}
        />
        <Field
          icon="fa-location-dot"
          placeholder="Physical Address / Location"
          value={form.location}
          onChange={update('location')}
        />
        <Field
          icon="fa-envelope"
          type="email"
          placeholder="Email"
          value={form.email}
          onChange={update('email')}
        />
        <Field
          icon="fa-phone"
          placeholder="+255 7XX XXX XXX"
          value={form.phone}
          onChange={handlePhoneChange}
        />
        <Field
          icon="fa-lock"
          type="password"
          placeholder="Password"
          value={form.password}
          onChange={update('password')}
        />
        <Field
          icon="fa-lock"
          type="password"
          placeholder="Confirm Password"
          value={form.password_confirmation}
          onChange={update('password_confirmation')}
        />

        <button
          type="submit"
          className="w-full bg-blue-700 hover:bg-blue-800 text-white font-semibold py-3 rounded-lg transition mt-2"
        >
          Continue →
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

function Field({ icon, type = 'text', placeholder, value, onChange }) {
  return (
    <div className="flex items-center border border-gray-300 rounded-lg px-3 py-2.5 focus-within:ring-2 focus-within:ring-blue-400">
      <i className={`fas ${icon} text-blue-600 mr-3 w-4`} />
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
