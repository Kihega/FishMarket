import { useQuery } from '@tanstack/react-query'
import { getOrders } from '../../api/orders'
import { Link } from 'react-router-dom'

const STATUS_STYLE = {
  pending:   'bg-yellow-100 text-yellow-700',
  received:  'bg-blue-100 text-blue-700',
  confirmed: 'bg-green-100 text-green-700',
  processed: 'bg-gray-100 text-gray-700',
  cancelled: 'bg-red-100 text-red-600',
}

export default function BuyerDashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ['my-orders'],
    queryFn: () => getOrders().then(r => r.data),
  })

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-blue-900 mb-6">My Orders</h1>
      <Link to="/" className="btn-primary mb-6 inline-block">Browse Marketplace</Link>

      {isLoading ? <p>Loading orders…</p> : (
        <div className="space-y-4">
          {data?.data?.map(order => (
            <div key={order.id} className="bg-white rounded-xl shadow p-5">
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-semibold">Order #{order.id} – {order.seller?.name}</p>
                  <p className="text-gray-500 text-sm">{order.items?.length} item(s) · TZS {Number(order.total_amount).toLocaleString()}</p>
                </div>
                <span className={`text-xs px-3 py-1 rounded-full font-medium ${STATUS_STYLE[order.status]}`}>
                  {order.status.toUpperCase()}
                </span>
              </div>
              {order.bill && (
                <p className="text-sm text-blue-600 mt-2">🧾 Bill #{order.bill.bill_number}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
