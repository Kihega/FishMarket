import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getSeller } from '../../api/sellers'
import { useAuthStore } from '../../store/authStore'
import OrderModal from '../../components/orders/OrderModal'
import { useState } from 'react'

export default function SellerPage() {
  const { id } = useParams()
  const { user } = useAuthStore()
  const [orderItem, setOrderItem] = useState(null)

  const { data, isLoading } = useQuery({
    queryKey: ['seller', id],
    queryFn: () => getSeller(id).then(r => r.data),
  })

  if (isLoading) return <div className="p-8">Loading seller…</div>

  const { seller, stocks, agencies } = data

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Seller Hero */}
      <div className="bg-white rounded-2xl shadow p-6 mb-8 flex gap-6 items-center">
        {seller.brand_logo
          ? <img src={`/storage/${seller.brand_logo}`} className="w-24 h-24 rounded-full object-cover border-4 border-blue-200" />
          : <div className="w-24 h-24 rounded-full bg-blue-100 flex items-center justify-center text-4xl">🐟</div>
        }
        <div>
          <h1 className="text-2xl font-bold text-blue-900">{seller.name}</h1>
          <p className="text-gray-500">🏢 {seller.office_address}</p>
          <p className="text-gray-500">📍 {seller.location_address}</p>
          {seller.bio && <p className="text-gray-600 mt-2">{seller.bio}</p>}
        </div>
      </div>

      {/* Fish Stock Grid */}
      <h2 className="text-xl font-bold text-blue-800 mb-4">Available Fish</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mb-8">
        {stocks.map(stock => (
          <div key={stock.id} className="bg-white rounded-xl shadow p-4">
            {stock.image && <img src={`/storage/${stock.image}`} className="w-full h-36 object-cover rounded-lg mb-3" />}
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">{stock.category?.name}</span>
            <h3 className="font-semibold text-blue-900 mt-1">{stock.fish_name}</h3>
            <p className="text-gray-600 text-sm">{stock.quantity_kg} kg available</p>
            <p className="text-blue-700 font-bold">TZS {Number(stock.price_per_kg).toLocaleString()} / kg</p>
            {user && (
              <button onClick={() => setOrderItem({ stock, seller, agencies })}
                className="mt-3 w-full bg-blue-600 text-white py-1.5 rounded-lg hover:bg-blue-700 text-sm">
                Order Now
              </button>
            )}
          </div>
        ))}
      </div>

      {orderItem && (
        <OrderModal data={orderItem} onClose={() => setOrderItem(null)} />
      )}
    </div>
  )
}
