import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import toast from 'react-hot-toast'
import client from '../../api/client'

export default function AdminPanel() {
  const [tab, setTab] = useState('stats')
  const qc = useQueryClient()

  const { data: stats } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => client.get('/admin/stats').then((r) => r.data),
  })

  const { data: users } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => client.get('/admin/users').then((r) => r.data),
    enabled: tab === 'users',
  })

  const { data: subscriptions } = useQuery({
    queryKey: ['admin-subscriptions'],
    queryFn: () => client.get('/admin/subscriptions').then((r) => r.data),
    enabled: tab === 'subscriptions',
  })

  const toggleUser = useMutation({
    mutationFn: (id) => client.put(`/admin/users/${id}/toggle`),
    onSuccess: () => {
      toast.success('User status updated')
      qc.invalidateQueries(['admin-users'])
    },
  })

  const confirmSubscription = useMutation({
    mutationFn: (id) => client.put(`/admin/subscriptions/${id}/confirm`),
    onSuccess: () => {
      toast.success('Subscription confirmed — seller activated')
      qc.invalidateQueries(['admin-subscriptions'])
    },
  })

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-blue-900 mb-6">Admin Panel</h1>

      <div className="flex gap-3 mb-6">
        {['stats', 'users', 'subscriptions'].map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg capitalize font-medium ${
              tab === t ? 'bg-blue-600 text-white' : 'bg-gray-100'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === 'stats' && stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total Users" value={stats.total_users} />
          <StatCard label="Active Sellers" value={stats.active_sellers} />
          <StatCard label="Total Buyers" value={stats.total_buyers} />
          <StatCard label="Pending Subscriptions" value={stats.pending_subscriptions} />
        </div>
      )}

      {tab === 'users' && (
        <div className="bg-white rounded-xl shadow divide-y">
          {users?.data?.map((u) => (
            <div key={u.id} className="flex justify-between items-center p-4">
              <div>
                <p className="font-semibold">{u.name} <span className="text-xs text-gray-400">({u.role})</span></p>
                <p className="text-sm text-gray-500">{u.email}</p>
              </div>
              <button
                onClick={() => toggleUser.mutate(u.id)}
                className={`text-sm px-3 py-1.5 rounded-lg ${
                  u.is_active ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'
                }`}
              >
                {u.is_active ? 'Deactivate' : 'Activate'}
              </button>
            </div>
          ))}
        </div>
      )}

      {tab === 'subscriptions' && (
        <div className="bg-white rounded-xl shadow divide-y">
          {subscriptions?.data?.map((s) => (
            <div key={s.id} className="flex justify-between items-center p-4">
              <div>
                <p className="font-semibold">{s.seller?.name}</p>
                <p className="text-sm text-gray-500 capitalize">
                  {s.plan} · TZS {Number(s.amount).toLocaleString()} · {s.status}
                </p>
              </div>
              {s.status === 'pending' && (
                <button
                  onClick={() => confirmSubscription.mutate(s.id)}
                  className="text-sm bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700"
                >
                  Confirm
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value }) {
  return (
    <div className="bg-white rounded-xl shadow p-5 text-center">
      <p className="text-3xl font-bold text-blue-700">{value ?? '—'}</p>
      <p className="text-sm text-gray-500 mt-1">{label}</p>
    </div>
  )
}
