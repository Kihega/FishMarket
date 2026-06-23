import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import client from '../../api/client'
import { useAuthStore } from '../../store/authStore'
import DashboardLayout from '../../components/dashboard/DashboardLayout'
import ChangePasswordModal from '../../components/dashboard/ChangePasswordModal'
import ModalShell from '../../components/auth/ModalShell'
import {
  HomeIcon, UsersIcon, StoreIcon, ActivityIcon, LockIcon, LogoutIcon,
} from '../../components/dashboard/Icons'

const SECTIONS = [
  { key: 'home', label: 'Home', icon: HomeIcon },
  { key: 'users', label: 'Manage Users', icon: UsersIcon },
  { key: 'sellers', label: 'Manage Sellers', icon: StoreIcon },
  { key: 'performance', label: 'System Performance', icon: ActivityIcon },
  { key: 'password', label: 'Change Password', icon: LockIcon },
  { key: 'logout', label: 'Logout', icon: LogoutIcon },
]

export default function AdminPanel() {
  const [active, setActive] = useState('home')
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const { clearAuth } = useAuthStore()

  const handleSelect = (key) => {
    if (key === 'logout') {
      clearAuth()
      window.location.href = '/'
      return
    }
    if (key === 'password') {
      setShowPasswordModal(true)
      return
    }
    setActive(key)
  }

  return (
    <>
      <DashboardLayout items={SECTIONS} activeKey={active} onSelect={handleSelect}>
        {active === 'home' && <HomePanel />}
        {active === 'users' && <UsersPanel />}
        {active === 'sellers' && <SellersPanel />}
        {active === 'performance' && <PerformancePanel />}
      </DashboardLayout>

      {showPasswordModal && (
        <ChangePasswordModal onClose={() => setShowPasswordModal(false)} />
      )}
    </>
  )
}

// ── HOME — overview stats ────────────────────────────────────────────
function HomePanel() {
  const { data } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => client.get('/admin/stats').then((r) => r.data),
  })

  return (
    <div>
      <h1 className="text-2xl font-bold text-blue-900 mb-6">Admin Overview</h1>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Users" value={data?.total_users} />
        <StatCard label="Active Sellers" value={data?.active_sellers} />
        <StatCard label="Total Buyers" value={data?.total_buyers} />
        <StatCard label="Pending Subscriptions" value={data?.pending_subscriptions} />
      </div>
    </div>
  )
}

function StatCard({ label, value }) {
  return (
    <div className="bg-white rounded-2xl shadow p-6 text-center">
      <p className="text-3xl font-bold text-blue-700">{value ?? '—'}</p>
      <p className="text-sm text-gray-500 mt-1">{label}</p>
    </div>
  )
}

// ── MANAGE USERS — list + suspend/delete + register-admin button ───
function UsersPanel() {
  const qc = useQueryClient()
  const [showRegisterAdmin, setShowRegisterAdmin] = useState(false)

  const { data: users } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => client.get('/admin/users').then((r) => r.data),
  })

  const toggleUser = useMutation({
    mutationFn: (id) => client.put(`/admin/users/${id}/toggle`),
    onSuccess: () => {
      toast.success('User status updated')
      qc.invalidateQueries(['admin-users'])
    },
  })

  const deleteUser = useMutation({
    mutationFn: (id) => client.delete(`/admin/users/${id}`),
    onSuccess: () => {
      toast.success('User deleted')
      qc.invalidateQueries(['admin-users'])
    },
    onError: (err) => toast.error(err.response?.data?.message || 'Could not delete user'),
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-blue-900">Manage Users</h1>
        <button onClick={() => setShowRegisterAdmin(true)} className="btn-primary">
          + Register Admin
        </button>
      </div>

      <div className="bg-white rounded-xl shadow divide-y">
        {users?.data?.map((u) => (
          <div key={u.id} className="flex flex-wrap justify-between items-center gap-3 p-4">
            <div>
              <p className="font-semibold">
                {u.name} <span className="text-xs text-gray-400 capitalize">({u.role})</span>
              </p>
              <p className="text-sm text-gray-500">{u.email}</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => toggleUser.mutate(u.id)}
                className={`text-sm px-3 py-1.5 rounded-lg ${
                  u.is_active ? 'bg-yellow-50 text-yellow-700' : 'bg-green-50 text-green-700'
                }`}
              >
                {u.is_active ? 'Suspend' : 'Activate'}
              </button>
              <button
                onClick={() => {
                  if (confirm(`Permanently delete ${u.name}? This cannot be undone.`)) {
                    deleteUser.mutate(u.id)
                  }
                }}
                className="text-sm px-3 py-1.5 rounded-lg bg-red-50 text-red-600"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {showRegisterAdmin && (
        <RegisterAdminModal onClose={() => setShowRegisterAdmin(false)} />
      )}
    </div>
  )
}

function RegisterAdminModal({ onClose }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({
    email: '', phone: '+255', password: '', password_confirmation: '',
  })
  const [error, setError] = useState('')

  const createAdmin = useMutation({
    mutationFn: (data) => client.post('/admin/users', data),
    onSuccess: () => {
      toast.success('New admin registered')
      qc.invalidateQueries(['admin-users'])
      onClose()
    },
    onError: (err) => setError(err.response?.data?.message || 'Failed to register admin'),
  })

  const handlePhoneChange = (e) => {
    let val = e.target.value
    if (!val.startsWith('+255')) val = '+255'
    setForm({ ...form, phone: val })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')
    if (form.password !== form.password_confirmation) {
      setError('Passwords do not match')
      return
    }
    createAdmin.mutate(form)
  }

  return (
    <ModalShell onClose={onClose}>
      <h2 className="text-xl font-bold text-blue-900 mb-4">Register New Admin</h2>

      {error && (
        <div className="bg-red-50 text-red-600 text-sm rounded-lg px-4 py-2 mb-4">{error}</div>
      )}

      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          type="email" required placeholder="Email" className="input"
          value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
        />
        <input
          placeholder="+255 7XX XXX XXX" className="input"
          value={form.phone} onChange={handlePhoneChange}
        />
        <input
          type="password" required placeholder="Password" className="input"
          value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
        />
        <input
          type="password" required placeholder="Confirm Password" className="input"
          value={form.password_confirmation}
          onChange={(e) => setForm({ ...form, password_confirmation: e.target.value })}
        />
        <button type="submit" disabled={createAdmin.isPending} className="btn-primary w-full">
          {createAdmin.isPending ? 'Creating…' : 'Register Admin'}
        </button>
      </form>
    </ModalShell>
  )
}

// ── MANAGE SELLERS — subscription/billing view ──────────────────────
function SellersPanel() {
  const qc = useQueryClient()

  const { data: subscriptions } = useQuery({
    queryKey: ['admin-subscriptions'],
    queryFn: () => client.get('/admin/subscriptions').then((r) => r.data),
  })

  const confirmSubscription = useMutation({
    mutationFn: (id) => client.put(`/admin/subscriptions/${id}/confirm`),
    onSuccess: () => {
      toast.success('Subscription confirmed — seller activated')
      qc.invalidateQueries(['admin-subscriptions'])
    },
  })

  return (
    <div>
      <h1 className="text-2xl font-bold text-blue-900 mb-6">Manage Seller Accounts</h1>
      <div className="bg-white rounded-xl shadow divide-y">
        {subscriptions?.data?.length ? (
          subscriptions.data.map((s) => (
            <div key={s.id} className="flex flex-wrap justify-between items-center gap-3 p-4">
              <div>
                <p className="font-semibold">{s.seller?.name}</p>
                <p className="text-sm text-gray-500 capitalize">
                  {s.plan} plan · TZS {Number(s.amount).toLocaleString()} ·{' '}
                  <span
                    className={
                      s.status === 'active'
                        ? 'text-green-600'
                        : s.status === 'pending'
                        ? 'text-yellow-600'
                        : 'text-gray-400'
                    }
                  >
                    {s.status}
                  </span>
                </p>
              </div>
              {s.status === 'pending' && (
                <button
                  onClick={() => confirmSubscription.mutate(s.id)}
                  className="btn-primary text-sm py-1.5"
                >
                  Confirm Payment
                </button>
              )}
            </div>
          ))
        ) : (
          <p className="text-gray-400 p-6 text-center">No subscriptions yet.</p>
        )}
      </div>
    </div>
  )
}

// ── SYSTEM PERFORMANCE — live polling metrics ───────────────────────
function PerformancePanel() {
  const { data } = useQuery({
    queryKey: ['admin-metrics'],
    queryFn: () => client.get('/admin/metrics').then((r) => r.data),
    refetchInterval: 5000, // live polling every 5s
  })

  return (
    <div>
      <h1 className="text-2xl font-bold text-blue-900 mb-2">System Performance</h1>
      <p className="text-gray-500 text-sm mb-6">
        Live application metrics · refreshes every 5 seconds
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard label="Active Users (15 min)" value={data?.active_users_last_15_min} />
        <StatCard label="Queries This Request" value={data?.queries_this_request} />
        <StatCard label="PHP Version" value={data?.php_version} />
        <StatCard label="Laravel Version" value={data?.laravel_version} />
      </div>

      <h2 className="text-lg font-bold text-blue-900 mb-3">Table Sizes</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Users" value={data?.table_sizes?.users} />
        <StatCard label="Fish Stocks" value={data?.table_sizes?.fish_stocks} />
        <StatCard label="Orders" value={data?.table_sizes?.orders} />
        <StatCard label="Subscriptions" value={data?.table_sizes?.subscriptions} />
      </div>

      {data?.server_time && (
        <p className="text-xs text-gray-400 mt-6">
          Server time: {new Date(data.server_time).toLocaleString()}
        </p>
      )}
    </div>
  )
}
