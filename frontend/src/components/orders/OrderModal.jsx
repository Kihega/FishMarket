import { useState } from 'react'
import { Smartphone, Landmark, Phone } from 'lucide-react'
import { placeOrder, payOrder } from '../../api/orders'
import { formatTsh } from '../../utils/currency'
import toast from 'react-hot-toast'

export default function OrderModal({ data: { stock, seller, agencies }, onClose }) {
  const [qty, setQty]       = useState(1)
  // '' = no agency chosen yet, 'self' = buyer will arrange their own
  // delivery, otherwise an agency id.
  const [agency, setAgency] = useState('')
  const [deliveryAddress, setDeliveryAddress] = useState('')
  const [method, setMethod] = useState('mobile')
  const [loading, setLoading] = useState(false)

  const hasAgencies = agencies?.length > 0
  const selectedAgency = agencies?.find((a) => String(a.id) === String(agency))
  const deliveryFee = selectedAgency ? Number(selectedAgency.delivery_fee) : 0
  const subtotal = qty * stock.price_per_kg
  const total = (subtotal + deliveryFee).toFixed(2)

  const handleOrder = async () => {
    // Agency selection is optional — the buyer may arrange their own
    // delivery. But once an agency IS chosen, the exact physical
    // delivery location is required so the agency knows where to go.
    if (selectedAgency && !deliveryAddress.trim()) {
      toast.error('Please enter the physical location for delivery')
      return
    }
    setLoading(true)
    try {
      const { data: order } = await placeOrder({
        seller_id: seller.id,
        items: [{ stock_id: stock.id, quantity_kg: qty }],
        payment_method: method,
        agency_id: selectedAgency ? selectedAgency.id : null,
        delivery_address: selectedAgency ? deliveryAddress.trim() : null,
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

        <label className="block text-sm mb-1">Delivery</label>
        {hasAgencies ? (
          <select value={agency} onChange={e => setAgency(e.target.value)} className="input mb-1">
            <option value="">I'll arrange my own delivery</option>
            {agencies.map(a => (
              <option key={a.id} value={a.id}>
                {a.agency_name} – {a.area_covered} ({formatTsh(a.delivery_fee)})
              </option>
            ))}
          </select>
        ) : (
          <p className="text-sm text-gray-500 mb-1">
            This seller has no delivery partner listed — you'll need to arrange your own delivery.
          </p>
        )}
        <p className="text-xs text-gray-400 mb-4">
          Choosing a delivery partner is optional — skip it if you have your own delivery arrangement.
        </p>

        {selectedAgency && (
          <>
            <label className="block text-sm mb-1">Delivery Location</label>
            <textarea
              value={deliveryAddress}
              onChange={e => setDeliveryAddress(e.target.value)}
              placeholder="Enter the exact physical location you want this order delivered to (street, landmark, area, etc.)"
              rows={2}
              className="input mb-4"
            />
          </>
        )}

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

        <div className="bg-blue-50 rounded-lg p-3 mb-4 space-y-1">
          <p className="text-sm text-blue-800 flex justify-between">
            <span>Fish subtotal</span><span>{formatTsh(subtotal)}</span>
          </p>
          <p className="text-sm text-blue-800 flex justify-between">
            <span>Delivery fee</span><span>{deliveryFee ? formatTsh(deliveryFee) : '—'}</span>
          </p>
          <p className="font-semibold text-blue-900 flex justify-between border-t border-blue-200 pt-1 mt-1">
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
