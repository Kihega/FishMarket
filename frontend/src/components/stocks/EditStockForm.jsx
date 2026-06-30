import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { updateStock } from '../../api/stocks'

// Replaces the old "Remove Stock" button. A seller can top up quantity
// on an existing item (including one that's reached 0.0kg) and/or
// change its price — never creates a new stock row. Items left at
// 0.0kg for 7 days are pruned automatically server-side, so there's no
// manual delete path here any more.
export default function EditStockForm({ stock, onDone }) {
  const qc = useQueryClient()
  const [addQty, setAddQty] = useState('')
  const [price, setPrice] = useState(stock.price_per_kg)

  const currentQty = Number(stock.quantity_kg)
  const newQty = currentQty + (Number(addQty) || 0)

  const save = useMutation({
    mutationFn: () => {
      const payload = {}
      if (addQty !== '' && Number(addQty) > 0) {
        payload.quantity_kg = newQty
      }
      if (price !== '' && Number(price) !== Number(stock.price_per_kg)) {
        payload.price_per_kg = Number(price)
      }
      return updateStock(stock.id, payload)
    },
    onSuccess: () => {
      toast.success('Stock updated!')
      qc.invalidateQueries({ queryKey: ['seller-stocks'] })
      onDone?.()
    },
    onError: () => toast.error('Failed to update stock'),
  })

  const nothingToSave = (addQty === '' || Number(addQty) <= 0)
    && Number(price) === Number(stock.price_per_kg)

  return (
    <div className="bg-white rounded-xl p-1">
      <h2 className="font-bold text-blue-900 mb-1">Edit {stock.fish_name}</h2>
      <p className="text-gray-500 text-sm mb-4">
        Currently {currentQty} kg in stock
        {stock.status === 'out_of_stock' && (
          <span className="text-red-500"> · out of stock</span>
        )}
      </p>

      <div className="grid grid-cols-1 gap-3">
        <div>
          <label className="text-sm text-gray-600">Add quantity (kg)</label>
          <input
            className="input mt-1" type="number" min="0" step="0.1"
            placeholder="0.0"
            value={addQty}
            onChange={(e) => setAddQty(e.target.value)}
          />
          {addQty !== '' && Number(addQty) > 0 && (
            <p className="text-xs text-gray-400 mt-1">New total: {newQty} kg</p>
          )}
        </div>
        <div>
          <label className="text-sm text-gray-600">Price per kg (Tsh)</label>
          <input
            className="input mt-1" type="number" min="0" step="1"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
          />
        </div>
      </div>

      <button
        onClick={() => save.mutate()}
        disabled={save.isPending || nothingToSave}
        className="mt-4 btn-primary w-full"
      >
        {save.isPending ? 'Saving…' : 'Save Changes'}
      </button>
    </div>
  )
}
