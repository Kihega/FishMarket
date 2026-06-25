import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Fish, MapPin, Receipt } from 'lucide-react'
import { getOrders } from '../../api/orders'
import { getSellers } from '../../api/sellers'
import { useAuthStore } from '../../store/authStore'
import { formatTsh } from '../../utils/currency'
import DashboardLayout from '../../components/dashboard/DashboardLayout'
import ChangePasswordModal from '../../components/dashboard/ChangePasswordModal'
import { HomeIcon, ClipboardListIcon, LockIcon, LogoutIcon } from '../../components/dashboard/Icons'

const SECTIONS = [
  { key: 'home', label: 'Home', icon: HomeIcon },
  { key: 'orders', label: 'My Orders', icon: ClipboardListIcon },
  { key: 'password', label: 'Change Password', icon: LockIcon },
  { key: 'logout', label: 'Logout', icon: LogoutIcon },
]

const STATUS_STYLE = {
  pending: 'bg-yellow-100 text-yellow-700',
  received: 'bg-blue-100 text-blue-700',
  confirmed: 'bg-green-100 text-green-700',
  processed: 'bg-gray-100 text-gray-700',
  cancelled: 'bg-red-100 text-red-600',
}

export default function BuyerDashboard() {
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
      </DashboardLayout>

      {showPasswordModal && (
        <ChangePasswordModal onClose={() => setShowPasswordModal(false)} />
      )}
    </>
  )
}

// ── HOME — browse registered seller platforms ───────────────────────
function HomePanel() {
  const { data, isLoading } = useQuery({
    queryKey: ['buyer-home-sellers'],
    queryFn: () => getSellers({}).then((r) => r.data),
  })

  return (
    <div>
      <h1 className="text-2xl font-bold text-blue-900 mb-2">Browse Markets</h1>
      <p className="text-gray-500 text-sm mb-6">
        Registered seller businesses on SmartFish
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
                {seller.brand_logo ? (
                  <img
                    src={seller.brand_logo.startsWith('data:') ? seller.brand_logo : `/storage/${seller.brand_logo}`}
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

// ── MY ORDERS — existing implementation, unchanged logic ────────────
function OrdersPanel() {
  const { data, isLoading } = useQuery({
    queryKey: ['my-orders'],
    queryFn: () => getOrders().then((r) => r.data),
  })

  return (
    <div>
      <h1 className="text-2xl font-bold text-blue-900 mb-6">My Orders</h1>

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
                </div>
                <span className={`text-xs px-3 py-1 rounded-full font-medium ${STATUS_STYLE[order.status]}`}>
                  {order.status.toUpperCase()}
                </span>
              </div>
              {order.bill && (
                <p className="text-sm text-blue-600 mt-2 flex items-center gap-1">
                  <Receipt className="w-4 h-4" /> Bill #{order.bill.bill_number}
                </p>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-gray-400 text-center py-10">No orders yet — browse the marketplace to get started.</p>
      )}
    </div>
  )
}
