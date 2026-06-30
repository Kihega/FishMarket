import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Fish, MapPin, Receipt } from 'lucide-react'
import { getOrders, cancelOrder, confirmDelivery } from '../../api/orders'
import { getSellers } from '../../api/sellers'
import { resolveImage } from '../../api/client'
import { useAuthStore } from '../../store/authStore'
import { formatTsh } from '../../utils/currency'
import DashboardLayout from '../../components/dashboard/DashboardLayout'
import ChangePasswordModal from '../../components/dashboard/ChangePasswordModal'
import { HomeIcon, ClipboardListIcon, LockIcon, LogoutIcon } from '../../components/dashboard/Icons'

const SECTIONS = [
  { key: 'home',     label: 'Home',            icon: HomeIcon },
  { key: 'orders',   label: 'My Orders',       icon: ClipboardListIcon },
  { key: 'password', label: 'Change Password', icon: LockIcon },
  { key: 'logout',   label: 'Logout',          icon: LogoutIcon },
]

const STATUS_STYLE = {
  pending:   'bg-yellow-100 text-yellow-700',
  received:  'bg-blue-100 text-blue-700',
  confirmed: 'bg-green-100 text-green-700',
  processed: 'bg-gray-100 text-gray-700',
  cancelled: 'bg-red-100 text-red-600',
}

// Buyers can self-cancel only within this many minutes of placing the
// order, and only before the seller has confirmed it — mirrors the
// backend's OrderController::CANCEL_WINDOW_MINUTES.
const CANCEL_WINDOW_MINUTES = 2

export default function BuyerDashboard() {
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
        {active === 'home'   && <HomePanel />}
        {active === 'orders' && <OrdersPanel />}
      </DashboardLayout>
      {showPasswordModal && <ChangePasswordModal onClose={() => setShowPasswordModal(false)} />}
    </>
  )
}

// ── HOME — browse seller platforms, refreshes every 15 s ─────────────
function HomePanel() {
  const { data, isLoading } = useQuery({
    queryKey: ['buyer-home-sellers'],
    queryFn: () => getSellers({}).then((r) => r.data),
    refetchInterval: 15000,          // live: new sellers appear within 15 s
    staleTime: 0,
  })

  return (
    <div>
      <h1 className="text-2xl font-bold text-blue-900 mb-2">Browse Markets</h1>
      <p className="text-gray-500 text-sm mb-6">
        Registered seller businesses on SmartFish · updates every 15 s
      </p>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-40 bg-gray-100 animate-pulse rounded-2xl" />
          ))}
        </div>
      ) : data?.data?.length ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {data.data.map((seller) => (
            <Link
              key={seller.id}
              to={`/sellers/${seller.id}`}
              className="bg-white rounded-2xl shadow p-5 hover:shadow-md transition flex flex-col gap-3"
            >
              <div className="flex items-center gap-3">
                {resolveImage(seller.brand_logo) ? (
                  <img
                    src={resolveImage(seller.brand_logo)}
                    alt={seller.name}
                    className="w-14 h-14 rounded-full object-cover border"
                  />
                ) : (
                  <div className="w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center">
                    <Fish className="w-6 h-6 text-blue-600" />
                  </div>
                )}
                <div>
                  <h3 className="font-bold text-blue-900">{seller.name}</h3>
                  <p className="text-gray-500 text-sm flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5" /> {seller.location_address || seller.location}
                  </p>
                </div>
              </div>
              <p className="text-sm text-blue-600">{seller.fish_stocks_count} items available</p>
            </Link>
          ))}
        </div>
      ) : (
        <p className="text-gray-400 text-center py-10">No sellers registered yet.</p>
      )}
    </div>
  )
}

// Whether an order is still inside the self-cancel window and not yet
// acted on by the seller.
function canCancel(order) {
  if (order.status !== 'pending' && order.status !== 'received') return false
  const ageMinutes = (Date.now() - new Date(order.created_at).getTime()) / 60000
  return ageMinutes <= CANCEL_WINDOW_MINUTES
}

// Whether the buyer can confirm delivery — seller has confirmed (or
// processed) the order and it hasn't already been marked delivered.
function canConfirmDelivery(order) {
  return (order.status === 'confirmed' || order.status === 'processed')
    && order.delivery?.delivery_status !== 'delivered'
}

// ── MY ORDERS — polls every 15 s ─────────────────────────────────────
function OrdersPanel() {
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['my-orders'],
    queryFn: () => getOrders().then((r) => r.data),
    refetchInterval: 15000,
    staleTime: 0,
  })

  const cancel = useMutation({
    mutationFn: (id) => cancelOrder(id),
    onSuccess: () => {
      toast.success('Order cancelled')
      qc.invalidateQueries({ queryKey: ['my-orders'] })
    },
    onError: (err) => {
      toast.error(err?.response?.data?.message || 'Could not cancel order')
    },
  })

  const confirmDeliveryMutation = useMutation({
    mutationFn: (id) => confirmDelivery(id),
    onSuccess: () => {
      toast.success('Delivery confirmed — thanks!')
      qc.invalidateQueries({ queryKey: ['my-orders'] })
    },
    onError: (err) => {
      toast.error(err?.response?.data?.message || 'Could not confirm delivery')
    },
  })

  return (
    <div>
      <h1 className="text-2xl font-bold text-blue-900 mb-2">My Orders</h1>
      <p className="text-gray-500 text-sm mb-6">Live order updates · refreshes every 15 s</p>

      {isLoading ? (
        <p className="text-gray-400">Loading orders…</p>
      ) : data?.data?.length ? (
        <div className="space-y-4">
          {data.data.map((order) => (
            <div key={order.id} className="bg-white rounded-xl shadow p-5">
              <div className="flex justify-between items-start flex-wrap gap-2">
                <div>
                  <p className="font-semibold">Order #{order.id} — {order.seller?.name}</p>
                  <p className="text-gray-500 text-sm">
                    {order.items?.length} item(s) · {formatTsh(order.total_amount)}
                  </p>
                  {order.delivery && (
                    <p className="text-xs text-gray-400 mt-1 capitalize">
                      Delivery: {order.delivery.delivery_status}
                    </p>
                  )}
                </div>
                <span className={`text-xs px-3 py-1 rounded-full font-medium ${STATUS_STYLE[order.status] ?? ''}`}>
                  {order.status?.toUpperCase()}
                </span>
              </div>
              {order.bill && (
                <p className="text-sm text-blue-600 mt-2 flex items-center gap-1">
                  <Receipt className="w-4 h-4" /> Bill #{order.bill.bill_number}
                </p>
              )}

              <div className="flex gap-3 mt-3">
                {canCancel(order) && (
                  <button
                    onClick={() => cancel.mutate(order.id)}
                    disabled={cancel.isPending}
                    className="text-red-500 text-sm hover:underline"
                  >
                    Cancel Order
                  </button>
                )}
                {canConfirmDelivery(order) && (
                  <button
                    onClick={() => confirmDeliveryMutation.mutate(order.id)}
                    disabled={confirmDeliveryMutation.isPending}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm"
                  >
                    Confirm Delivery
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-gray-400 text-center py-10">
          No orders yet — browse the marketplace to get started.
        </p>
      )}
    </div>
  )
}
