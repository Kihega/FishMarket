import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createStock } from '../../api/stocks'
import toast from 'react-hot-toast'

// Image upload was removed from this form entirely — it was crashing
// the page. Stocks can still be added with no photo (the backend
// already treats the image field as optional).
export default function AddStockForm({ onDone }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({
    fish_name: '', quantity_kg: '', price_per_kg: '',
  })

  const add = useMutation({
    mutationFn: () => createStock(form),
    onSuccess: () => {
      toast.success('Stock added!')
      qc.invalidateQueries(['seller-stocks'])
      setForm({ fish_name: '', quantity_kg: '', price_per_kg: '' })
      onDone?.()
    },
    onError: () => toast.error('Failed to add stock'),
  })

  return (
    <div className="bg-white rounded-xl p-1">
      <h2 className="font-bold text-blue-900 mb-4">Add Fish Stock</h2>

      <div className="grid grid-cols-2 gap-3">
        <input
          className="input col-span-2" placeholder="Fish name"
          value={form.fish_name}
          onChange={(e) => setForm({ ...form, fish_name: e.target.value })}
        />
        <input
          className="input" type="number" min="0.1" step="0.1" placeholder="Quantity (kg)"
          value={form.quantity_kg}
          onChange={(e) => setForm({ ...form, quantity_kg: e.target.value })}
        />
        <input
          className="input" type="number" min="0" step="1" placeholder="Price per kg (Tsh)"
          value={form.price_per_kg}
          onChange={(e) => setForm({ ...form, price_per_kg: e.target.value })}
        />
      </div>

      <button
        onClick={() => add.mutate()}
        disabled={add.isPending || !form.fish_name}
        className="mt-4 btn-primary w-full"
      >
        {add.isPending ? 'Adding…' : 'Add Stock'}
      </button>
    </div>
  )
}
