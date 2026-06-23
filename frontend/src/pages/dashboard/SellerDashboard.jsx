import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import client from '../../api/client'
import { getOrders, confirmOrder } from '../../api/orders'
import { getStocks, deleteStock } from '../../api/stocks'
import { useAuthStore } from '../../store/authStore'
import DashboardLayout from '../../components/dashboard/DashboardLayout'
import ChangePasswordModal from '../../components/dashboard/ChangePasswordModal'
import ModalShell from '../../components/auth/ModalShell'
import AddStockForm from '../../components/stocks/AddStockForm'
import {
  HomeIcon, ClipboardListIcon, PackageIcon, ContactIcon, TruckIcon, LockIcon, LogoutIcon,
} from '../../components/dashboard/Icons'

const SECTIONS = [
  { key: 'home', label: 'Home', icon: HomeIcon },
  { key: 'orders', label: 'Manage Orders', icon: ClipboardListIcon },
  { key: 'stocks', label: 'Manage Stocks', icon: PackageIcon },
  { key: 'buyers', label: 'Manage Buyers', icon: ContactIcon },
  { key: 'agencies', label: 'Delivery Partners', icon: TruckIcon },
  { key: 'password', label: 'Change Password', icon: LockIcon },
  { key: 'logout', label: 'Logout', icon: LogoutIcon },
]

export default function SellerDashboard() {
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
        {active === 'orders' && <OrdersPanel />}
        {active === 'stocks' && <StocksPanel />}
        {active === 'buyers' && <BuyersPanel />}
        {active === 'agencies' && <AgenciesPanel />}
      </DashboardLayout>

      {showPasswordModal && (
        <ChangePasswordModal onClose={() => setShowPasswordModal(false)} />
      )}
    </>
  )
}

// ── HOME — quick overview + profile/brand logo setup ───────────────
function HomePanel() {
  const { user, setAuth } = useAuthStore()
  const [logoFile, setLogoFile] = useState(null)
  const [logoPreview, setLogoPreview] = useState(null)

  const { data: orders } = useQuery({
    queryKey: ['seller-orders'],
    queryFn: () => getOrders().then((r) => r.data),
  })
  const { data: stocks } = useQuery({
    queryKey: ['seller-stocks'],
    queryFn: () => getStocks({}).then((r) => r.data),
  })

  const pendingCount = orders?.data?.filter((o) => o.status === 'pending' || o.status === 'received').length ?? 0
  const stockCount = stocks?.data?.length ?? 0

  const handleLogoChange = (e) => {
    const file = e.target.files[0]
    setLogoFile(file)
    setLogoPreview(file ? URL.createObjectURL(file) : null)
  }

  const uploadLogo = useMutation({
    mutationFn: () => {
      const fd = new FormData()
      fd.append('brand_logo', logoFile)
      return client.put('/seller/profile', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    },
    onSuccess: (res) => {
      toast.success('Brand logo updated')
      setAuth(res.data, useAuthStore.getState().token)
      setLogoFile(null)
      setLogoPreview(null)
    },
    onError: () => toast.error('Failed to upload logo'),
  })

  return (
    <div>
      <h1 className="text-2xl font-bold text-blue-900 mb-6">Welcome back</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Pending Orders" value={pendingCount} />
        <StatCard label="Active Stock Items" value={stockCount} />
        <StatCard label="Total Orders" value={orders?.data?.length ?? 0} />
      </div>

      <div className="bg-white rounded-xl shadow p-5 max-w-md">
        <h2 className="font-bold text-blue-900 mb-3">Business Brand Logo</h2>
        <div className="flex items-center gap-4">
          <div className="w-20 h-20 rounded-full border-2 border-dashed border-gray-300 flex items-center justify-center overflow-hidden bg-gray-50 flex-shrink-0">
            {logoPreview ? (
              <img src={logoPreview} alt="Preview" className="w-full h-full object-cover" />
            ) : user?.brand_logo ? (
              <img src={`/storage/${user.brand_logo}`} alt="Current logo" className="w-full h-full object-cover" />
            ) : (
              <span className="text-gray-400 text-xs text-center px-1">No logo</span>
            )}
          </div>
          <div className="flex-1">
            <input type="file" accept="image/*" onChange={handleLogoChange} className="input text-sm" />
            {logoFile && (
              <button
                onClick={() => uploadLogo.mutate()}
                disabled={uploadLogo.isPending}
                className="btn-primary mt-2 text-sm py-1.5 w-full"
              >
                {uploadLogo.isPending ? 'Uploading…' : 'Save Logo'}
              </button>
            )}
          </div>
        </div>
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

// ── MANAGE ORDERS — live, polling every 15s ─────────────────────────
function OrdersPanel() {
  const qc = useQueryClient()

  const { data: orders } = useQuery({
    queryKey: ['seller-orders'],
    queryFn: () => getOrders().then((r) => r.data),
    refetchInterval: 15000,
  })

  const confirm = useMutation({
    mutationFn: (id) => confirmOrder(id),
    onSuccess: () => {
      toast.success('Order confirmed!')
      qc.invalidateQueries(['seller-orders'])
    },
  })

  return (
    <div>
      <h1 className="text-2xl font-bold text-blue-900 mb-2">Manage Orders</h1>
      <p className="text-gray-500 text-sm mb-6">Live order updates · refreshes every 15 seconds</p>

      <div className="space-y-4">
        {orders?.data?.length ? (
          orders.data.map((order) => (
            <div key={order.id} className="bg-white rounded-xl shadow p-4 flex justify-between items-center flex-wrap gap-3">
              <div>
                <p className="font-semibold">Order #{order.id} — {order.buyer?.name}</p>
                <p className="text-gray-500 text-sm">
                  TZS {Number(order.total_amount).toLocaleString()} · {order.payment_status}
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

// ── MANAGE STOCKS — dynamic responsive card grid ────────────────────
function StocksPanel() {
  const qc = useQueryClient()
  const [showAddForm, setShowAddForm] = useState(false)

  const { data: stocks } = useQuery({
    queryKey: ['seller-stocks'],
    queryFn: () => getStocks({}).then((r) => r.data),
  })

  const remove = useMutation({
    mutationFn: (id) => deleteStock(id),
    onSuccess: () => {
      toast.success('Stock removed')
      qc.invalidateQueries(['seller-stocks'])
    },
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-blue-900">Manage Stocks</h1>
        <button onClick={() => setShowAddForm(true)} className="btn-primary">
          + Add New Stock
        </button>
      </div>

      {/*
        Dynamic responsive grid: card count per row adapts to screen
        size automatically via Tailwind's grid-cols breakpoints —
        1 col on mobile, 2 on tablet, 3 on desktop, 4 on wide screens.
      */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
        {stocks?.data?.length ? (
          stocks.data.map((s) => (
            <div key={s.id} className="bg-white rounded-xl shadow p-4 flex flex-col">
              {s.image && (
                <img
                  src={`/storage/${s.image}`}
                  alt={s.fish_name}
                  className="w-full h-32 object-cover rounded-lg mb-3"
                />
              )}
              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full self-start mb-1">
                {s.category?.name}
              </span>
              <p className="font-semibold">{s.fish_name}</p>
              <p className="text-gray-500 text-sm">
                {s.quantity_kg} kg · TZS {Number(s.price_per_kg).toLocaleString()}/kg
              </p>
              <span
                className={`text-xs mt-1 ${
                  s.status === 'active' ? 'text-green-600' : 'text-red-500'
                }`}
              >
                {s.status === 'active' ? '● In Stock' : '● Out of Stock'}
              </span>
              <button
                onClick={() => remove.mutate(s.id)}
                className="mt-3 text-red-500 text-sm hover:underline self-start"
              >
                Remove Stock
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
          <AddStockForm onDone={() => setShowAddForm(false)} />
        </ModalShell>
      )}
    </div>
  )
}

// ── MANAGE BUYERS — live buyer activity on this seller's platform ───
function BuyersPanel() {
  const { data: buyers } = useQuery({
    queryKey: ['seller-buyers'],
    queryFn: () => client.get('/seller/buyers').then((r) => r.data),
    refetchInterval: 15000,
  })

  return (
    <div>
      <h1 className="text-2xl font-bold text-blue-900 mb-2">Manage Buyers</h1>
      <p className="text-gray-500 text-sm mb-6">
        Buyers who have placed orders on your platform · live updates
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

// ── DELIVERY PARTNERS — manage agencies ──────────────────────────────
function AgenciesPanel() {
  const qc = useQueryClient()
  const [form, setForm] = useState({ agency_name: '', contact: '', area_covered: '' })

  const { data: agencies } = useQuery({
    queryKey: ['seller-agencies'],
    queryFn: () => client.get('/agencies').then((r) => r.data),
  })

  const addAgency = useMutation({
    mutationFn: (data) => client.post('/agencies', data),
    onSuccess: () => {
      toast.success('Delivery partner added')
      qc.invalidateQueries(['seller-agencies'])
      setForm({ agency_name: '', contact: '', area_covered: '' })
    },
  })

  const removeAgency = useMutation({
    mutationFn: (id) => client.delete(`/agencies/${id}`),
    onSuccess: () => {
      toast.success('Delivery partner removed')
      qc.invalidateQueries(['seller-agencies'])
    },
  })

  return (
    <div>
      <h1 className="text-2xl font-bold text-blue-900 mb-6">Delivery Partners</h1>

      <div className="bg-white rounded-xl shadow p-5 mb-6">
        <h2 className="font-bold text-blue-900 mb-3">Add Delivery Partner</h2>
        <div className="grid sm:grid-cols-3 gap-3">
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
                <p className="text-sm text-gray-500">{a.contact} · {a.area_covered}</p>
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
