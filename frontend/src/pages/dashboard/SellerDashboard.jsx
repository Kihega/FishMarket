import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getOrders, confirmOrder } from '../../api/orders'
import { getStocks, deleteStock } from '../../api/stocks'
import toast from 'react-hot-toast'
import AddStockForm from '../../components/stocks/AddStockForm'

export default function SellerDashboard() {
  const [tab, setTab] = useState('orders')
  const qc = useQueryClient()

  const { data: orders } = useQuery({ queryKey: ['seller-orders'], queryFn: () => getOrders().then(r=>r.data) })
  const { data: stocks } = useQuery({ queryKey: ['seller-stocks'], queryFn: () => getStocks({}).then(r=>r.data) })

  const confirm = useMutation({
    mutationFn: (id) => confirmOrder(id),
    onSuccess: () => { toast.success('Order confirmed!'); qc.invalidateQueries(['seller-orders']) },
  })

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-blue-900 mb-4">Seller Dashboard</h1>

      <div className="flex gap-3 mb-6">
        {['orders','stocks'].map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg capitalize font-medium ${tab===t ? 'bg-blue-600 text-white' : 'bg-gray-100'}`}>
            {t}
          </button>
        ))}
      </div>

      {tab === 'orders' && (
        <div className="space-y-4">
          {orders?.data?.map(order => (
            <div key={order.id} className="bg-white rounded-xl shadow p-4 flex justify-between items-center">
              <div>
                <p className="font-semibold">Order #{order.id} – {order.buyer?.name}</p>
                <p className="text-gray-500 text-sm">TZS {Number(order.total_amount).toLocaleString()} · {order.payment_status}</p>
                <p className="text-sm capitalize">Status: {order.status}</p>
              </div>
              {order.payment_status === 'paid' && order.status === 'received' && (
                <button onClick={() => confirm.mutate(order.id)}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm">
                  Confirm
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {tab === 'stocks' && (
        <div>
          <AddStockForm />
          <div className="mt-6 space-y-3">
            {stocks?.data?.map(s => (
              <div key={s.id} className="bg-white rounded-xl shadow p-4 flex justify-between items-center">
                <div>
                  <p className="font-semibold">{s.fish_name} ({s.category?.name})</p>
                  <p className="text-gray-500 text-sm">{s.quantity_kg} kg · TZS {Number(s.price_per_kg).toLocaleString()}/kg</p>
                </div>
                <button onClick={() => deleteStock(s.id).then(() => qc.invalidateQueries(['seller-stocks']))}
                  className="text-red-500 text-sm hover:underline">Remove</button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
