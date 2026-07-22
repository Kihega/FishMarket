import { useState } from 'react'
import { Smartphone, Landmark, Phone } from 'lucide-react'
import { placeOrder, payOrder } from '../../api/orders'
import { formatTsh } from '../../utils/currency'
import toast from 'react-hot-toast'

// Delivery itself isn't arranged through the app — the seller sees
// the buyer's phone number on the order (every buyer account has one)
// and calls them directly to sort out where/how to deliver.
export default function OrderModal({ data: { stock, seller }, onClose }) {
  const [qty, setQty]       = useState(1)
  const [method, setMethod] = useState('mobile')
  const [loading, setLoading] = useState(false)

  const total = (qty * stock.price_per_kg).toFixed(2)

  const handleOrder = async () => {
    setLoading(true)
    try {
      const { data: order } = await placeOrder({
        seller_id: seller.id,
        items: [{ stock_id: stock.id, quantity_kg: qty }],
        payment_method: method,
      })
      await payOrder(order.id)   // mark as paid immediately (demo flow)
      toast.success('Order placed & payment recorded!')
      onClose()
    } catch (e) {
      toast.error(e.response?.data?.message || 'Order failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl">
        <h2 className="text-xl font-bold mb-4">Place Order – {stock.fish_name}</h2>

        <label className="block text-sm mb-1">Quantity (kg)</label>
        <input type="number" min="0.1" max={stock.quantity_kg} step="0.1"
          value={qty} onChange={e => setQty(Number(e.target.value))}
          className="input mb-4" />

        <label className="block text-sm mb-1">Payment Method</label>
        <div className="flex gap-4 mb-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="radio" value="mobile" checked={method === 'mobile'} onChange={() => setMethod('mobile')} />
            <Smartphone className="w-4 h-4" /> Mobile Money
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="radio" value="bank" checked={method === 'bank'} onChange={() => setMethod('bank')} />
            <Landmark className="w-4 h-4" /> Bank Transfer
          </label>
        </div>

        {method === 'mobile' && seller.phone && (
          <div className="bg-green-50 text-green-800 rounded-lg p-3 mb-4 flex items-center gap-2 text-sm">
            <Phone className="w-4 h-4 flex-shrink-0" />
            Send mobile money to the seller at <span className="font-semibold">{seller.phone}</span>
          </div>
        )}

        <p className="text-xs text-gray-400 mb-4">
          The seller will call the phone number on your account to arrange delivery.
        </p>

        <div className="bg-blue-50 rounded-lg p-3 mb-4 space-y-1">
          <p className="font-semibold text-blue-900 flex justify-between">
            <span>Total</span><span>{formatTsh(total)}</span>
          </p>
        </div>

        <div className="flex gap-3">
          <button onClick={onClose} className="flex-1 border border-gray-300 rounded-lg py-2">Cancel</button>
          <button onClick={handleOrder} disabled={loading}
            className="flex-1 bg-blue-600 text-white rounded-lg py-2 hover:bg-blue-700 disabled:opacity-50">
            {loading ? 'Placing…' : 'Confirm Order'}
          </button>
        </div>
      </div>
    </div>
  )
}
