import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import client, { resolveImage } from '../../api/client'
import { getOrders, confirmOrder } from '../../api/orders'
import { getMyStocks } from '../../api/stocks'
import { useAuthStore } from '../../store/authStore'
import { formatTsh } from '../../utils/currency'
import DashboardLayout from '../../components/dashboard/DashboardLayout'
import ChangePasswordModal from '../../components/dashboard/ChangePasswordModal'
import ModalShell from '../../components/auth/ModalShell'
import AddStockForm from '../../components/stocks/AddStockForm'
import EditStockForm from '../../components/stocks/EditStockForm'
import {
  HomeIcon, ClipboardListIcon, PackageIcon, ContactIcon,
  TruckIcon, LockIcon, LogoutIcon,
} from '../../components/dashboard/Icons'

const SECTIONS = [
  { key: 'home',     label: 'Home',              icon: HomeIcon },
  { key: 'orders',   label: 'Manage Orders',     icon: ClipboardListIcon },
  { key: 'stocks',   label: 'Manage Stocks',     icon: PackageIcon },
  { key: 'buyers',   label: 'Manage Buyers',     icon: ContactIcon },
  { key: 'agencies', label: 'Delivery Partners', icon: TruckIcon },
  { key: 'password', label: 'Change Password',   icon: LockIcon },
  { key: 'logout',   label: 'Logout',            icon: LogoutIcon },
]

export default function SellerDashboard() {
  const [active, setActive] = useState('home')
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const { clearAuth } = useAuthStore()

  const handleSelect = (key) => {
    if (key === 'logout') { clearAuth(); window.location.href = '/'; return }
    if (key === 'password') { setShowPasswordModal(true); return }
    setActive(key)
  }

  return (
    <>
      <DashboardLayout items={SECTIONS} activeKey={active} onSelect={handleSelect}>
        {active === 'home'     && <HomePanel />}
        {active === 'orders'   && <OrdersPanel />}
        {active === 'stocks'   && <StocksPanel />}
        {active === 'buyers'   && <BuyersPanel />}
        {active === 'agencies' && <AgenciesPanel />}
      </DashboardLayout>
      {showPasswordModal && <ChangePasswordModal onClose={() => setShowPasswordModal(false)} />}
    </>
  )
}

// ── HOME — quick stats overview (polls every 30 s) ────────────────────
function HomePanel() {
  const { data: orders } = useQuery({
    queryKey: ['seller-orders'],
    queryFn: () => getOrders().then((r) => r.data),
    refetchInterval: 30000,
    staleTime: 0,
  })
  const { data: stocks } = useQuery({
    queryKey: ['seller-stocks'],
    queryFn: () => getMyStocks().then((r) => r.data),
    refetchInterval: 30000,
    staleTime: 0,
  })

  const pendingCount = orders?.data?.filter(
    (o) => o.status === 'pending' || o.status === 'received'
  ).length ?? 0

  return (
    <div>
      <h1 className="text-2xl font-bold text-blue-900 mb-6">Welcome back</h1>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Pending Orders"    value={pendingCount} />
        <StatCard label="Active Stock Items" value={stocks?.data?.length ?? 0} />
        <StatCard label="Total Orders"       value={orders?.data?.length ?? 0} />
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

// ── MANAGE ORDERS — polls every 10 s ─────────────────────────────────
function OrdersPanel() {
  const qc = useQueryClient()

  const { data: orders } = useQuery({
    queryKey: ['seller-orders'],
    queryFn: () => getOrders().then((r) => r.data),
    refetchInterval: 10000,      // new orders appear within 10 s
    staleTime: 0,
  })

  const confirm = useMutation({
    mutationFn: (id) => confirmOrder(id),
    onSuccess: () => {
      toast.success('Order confirmed!')
      qc.invalidateQueries({ queryKey: ['seller-orders'] })
    },
  })

  return (
    <div>
      <h1 className="text-2xl font-bold text-blue-900 mb-2">Manage Orders</h1>
      <p className="text-gray-500 text-sm mb-6">Live order updates · refreshes every 10 s</p>

      <div className="space-y-4">
        {orders?.data?.length ? (
          orders.data.map((order) => (
            <div
              key={order.id}
              className="bg-white rounded-xl shadow p-4 flex justify-between items-center flex-wrap gap-3"
            >
              <div>
                <p className="font-semibold">Order #{order.id} — {order.buyer?.name}</p>
                <p className="text-gray-500 text-sm">
                  {formatTsh(order.total_amount)} · {order.payment_status}
                </p>
                <p className="text-sm capitalize">Status: {order.status}</p>
              </div>
              {order.payment_status === 'paid' && order.status === 'received' && (
                <button
                  onClick={() => confirm.mutate(order.id)}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm"
                >
                  Confirm
                </button>
              )}
            </div>
          ))
        ) : (
          <p className="text-gray-400 text-center py-10">No orders yet.</p>
        )}
      </div>
    </div>
  )
}

// ── MANAGE STOCKS — polls every 15 s ─────────────────────────────────
function StocksPanel() {
  const qc = useQueryClient()
  const [showAddForm, setShowAddForm] = useState(false)
  const [editingStock, setEditingStock] = useState(null)

  const { data: stocks } = useQuery({
    queryKey: ['seller-stocks'],
    queryFn: () => getMyStocks().then((r) => r.data),
    refetchInterval: 15000,
    staleTime: 0,
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-blue-900">Manage Stocks</h1>
          <p className="text-gray-500 text-sm">Live updates · refreshes every 15 s</p>
        </div>
        <button onClick={() => setShowAddForm(true)} className="btn-primary">
          + Add New Stock
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
        {stocks?.data?.length ? (
          stocks.data.map((s) => (
            <div key={s.id} className="bg-white rounded-xl shadow p-4 flex flex-col">
              {resolveImage(s.image) && (
                <img
                  src={resolveImage(s.image)}
                  alt={s.fish_name}
                  className="w-full h-32 object-cover rounded-lg mb-3"
                />
              )}
              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full self-start mb-1">
                {s.category?.name}
              </span>
              <p className="font-semibold">{s.fish_name}</p>
              <p className="text-gray-500 text-sm">
                {s.quantity_kg} kg · {formatTsh(s.price_per_kg)}/kg
              </p>
              <span className={`text-xs mt-1 ${s.status === 'active' ? 'text-green-600' : 'text-red-500'}`}>
                {s.status === 'active' ? '● In Stock' : '● Out of Stock'}
              </span>
              <button
                onClick={() => setEditingStock(s)}
                className="mt-3 text-blue-600 text-sm hover:underline self-start"
              >
                Edit Stock
              </button>
            </div>
          ))
        ) : (
          <p className="text-gray-400 col-span-full text-center py-10">
            No stock items yet — add your first one above.
          </p>
        )}
      </div>

      {showAddForm && (
        <ModalShell onClose={() => setShowAddForm(false)} maxWidth="max-w-lg">
          <AddStockForm onDone={() => { setShowAddForm(false); qc.invalidateQueries({ queryKey: ['seller-stocks'] }) }} />
        </ModalShell>
      )}

      {editingStock && (
        <ModalShell onClose={() => setEditingStock(null)} maxWidth="max-w-lg">
          <EditStockForm
            stock={editingStock}
            onDone={() => { setEditingStock(null); qc.invalidateQueries({ queryKey: ['seller-stocks'] }) }}
          />
        </ModalShell>
      )}
    </div>
  )
}

// ── MANAGE BUYERS — polls every 10 s ─────────────────────────────────
function BuyersPanel() {
  const { data: buyers } = useQuery({
    queryKey: ['seller-buyers'],
    queryFn: () => client.get('/seller/buyers').then((r) => r.data),
    refetchInterval: 10000,
    staleTime: 0,
  })

  return (
    <div>
      <h1 className="text-2xl font-bold text-blue-900 mb-2">Manage Buyers</h1>
      <p className="text-gray-500 text-sm mb-6">
        Buyers who have placed orders on your platform · live updates every 10 s
      </p>

      <div className="bg-white rounded-xl shadow divide-y">
        {buyers?.length ? (
          buyers.map((b) => (
            <div key={b.order_id} className="flex flex-wrap justify-between items-center gap-3 p-4">
              <div>
                <p className="font-semibold">{b.buyer_name}</p>
                <p className="text-sm text-gray-500">{b.buyer_phone} · {b.buyer_email}</p>
                <p className="text-xs text-gray-400 mt-1">
                  Ordered {new Date(b.ordered_at).toLocaleString()}
                </p>
              </div>
              <div className="text-right">
                <span className="text-xs capitalize bg-blue-50 text-blue-700 px-2 py-1 rounded-full">
                  {b.order_status}
                </span>
                <p className="text-xs text-gray-400 mt-1 capitalize">
                  Delivery: {b.delivery_status}
                </p>
                {b.delivery_address && (
                  <p className="text-xs text-gray-400 mt-1 max-w-xs text-right">
                    Deliver to: {b.delivery_address}
                  </p>
                )}
              </div>
            </div>
          ))
        ) : (
          <p className="text-gray-400 p-6 text-center">No buyers yet.</p>
        )}
      </div>
    </div>
  )
}

// ── DELIVERY PARTNERS — polls every 15 s ─────────────────────────────
function AgenciesPanel() {
  const qc = useQueryClient()
  const [form, setForm] = useState({ agency_name: '', contact: '', area_covered: '', delivery_fee: '' })

  const { data: agencies } = useQuery({
    queryKey: ['seller-agencies'],
    queryFn: () => client.get('/agencies').then((r) => r.data),
    refetchInterval: 15000,
    staleTime: 0,
  })

  const addAgency = useMutation({
    mutationFn: (data) => client.post('/agencies', data),
    onSuccess: () => {
      toast.success('Delivery partner added')
      qc.invalidateQueries({ queryKey: ['seller-agencies'] })
      setForm({ agency_name: '', contact: '', area_covered: '', delivery_fee: '' })
    },
  })

  const removeAgency = useMutation({
    mutationFn: (id) => client.delete(`/agencies/${id}`),
    onSuccess: () => {
      toast.success('Delivery partner removed')
      qc.invalidateQueries({ queryKey: ['seller-agencies'] })
    },
  })

  return (
    <div>
      <h1 className="text-2xl font-bold text-blue-900 mb-6">Delivery Partners</h1>

      <div className="bg-white rounded-xl shadow p-5 mb-6">
        <h2 className="font-bold text-blue-900 mb-3">Add Delivery Partner</h2>
        <div className="grid sm:grid-cols-4 gap-3">
          <input
            placeholder="Agency Name" className="input"
            value={form.agency_name}
            onChange={(e) => setForm({ ...form, agency_name: e.target.value })}
          />
          <input
            placeholder="Contact" className="input"
            value={form.contact}
            onChange={(e) => setForm({ ...form, contact: e.target.value })}
          />
          <input
            placeholder="Area Covered" className="input"
            value={form.area_covered}
            onChange={(e) => setForm({ ...form, area_covered: e.target.value })}
          />
          <input
            placeholder="Delivery Fee (Tsh)" className="input" type="number" min="0" step="1"
            value={form.delivery_fee}
            onChange={(e) => setForm({ ...form, delivery_fee: e.target.value })}
          />
        </div>
        <button
          onClick={() => addAgency.mutate(form)}
          disabled={!form.agency_name || addAgency.isPending}
          className="btn-primary mt-3"
        >
          {addAgency.isPending ? 'Adding…' : 'Add Partner'}
        </button>
      </div>

      <div className="bg-white rounded-xl shadow divide-y">
        {agencies?.length ? (
          agencies.map((a) => (
            <div key={a.id} className="flex justify-between items-center p-4">
              <div>
                <p className="font-semibold">{a.agency_name}</p>
                <p className="text-sm text-gray-500">
                  {a.contact} · {a.area_covered} · {formatTsh(a.delivery_fee)} delivery fee
                </p>
              </div>
              <button
                onClick={() => removeAgency.mutate(a.id)}
                className="text-red-500 text-sm hover:underline"
              >
                Remove
              </button>
            </div>
          ))
        ) : (
          <p className="text-gray-400 p-6 text-center">No delivery partners yet.</p>
        )}
      </div>
    </div>
  )
}
