import { useState } from 'react'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { createStock } from '../../api/stocks'
import client from '../../api/client'
import toast from 'react-hot-toast'

export default function AddStockForm({ onDone }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({
    fish_name: '', category_id: '', quantity_kg: '', price_per_kg: '',
  })
  const [image, setImage] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)

  const { data: cats } = useQuery({
    queryKey: ['categories'],
    queryFn: () => client.get('/categories').then((r) => r.data),
  })

  const handleImageChange = (e) => {
    const file = e.target.files[0]
    setImage(file)
    setImagePreview(file ? URL.createObjectURL(file) : null)
  }

  const add = useMutation({
    mutationFn: () => {
      const fd = new FormData()
      Object.entries(form).forEach(([k, v]) => fd.append(k, v))
      if (image) fd.append('image', image)
      return createStock(fd)
    },
    onSuccess: () => {
      toast.success('Stock added!')
      qc.invalidateQueries(['seller-stocks'])
      setForm({ fish_name: '', category_id: '', quantity_kg: '', price_per_kg: '' })
      setImage(null)
      setImagePreview(null)
      onDone?.()
    },
    onError: () => toast.error('Failed to add stock'),
  })

  return (
    <div className="bg-white rounded-xl p-1">
      <h2 className="font-bold text-blue-900 mb-4">Add Fish Stock</h2>

      <div className="grid grid-cols-2 gap-3">
        <select
          className="input col-span-2"
          value={form.category_id}
          onChange={(e) => setForm({ ...form, category_id: e.target.value })}
        >
          <option value="">Select category…</option>
          {cats?.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
        <input
          className="input" placeholder="Fish name"
          value={form.fish_name}
          onChange={(e) => setForm({ ...form, fish_name: e.target.value })}
        />
        <input
          className="input" type="number" placeholder="Qty (kg)"
          value={form.quantity_kg}
          onChange={(e) => setForm({ ...form, quantity_kg: e.target.value })}
        />
        <input
          className="input" type="number" placeholder="Price/kg"
          value={form.price_per_kg}
          onChange={(e) => setForm({ ...form, price_per_kg: e.target.value })}
        />

        {/* Image upload with visible placeholder + live preview */}
        <div className="col-span-2">
          <label className="block text-sm text-gray-500 mb-1">Fish Photo</label>
          <div className="flex items-center gap-3">
            <div className="w-20 h-20 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center overflow-hidden bg-gray-50 flex-shrink-0">
              {imagePreview ? (
                <img src={imagePreview} alt="Preview" className="w-full h-full object-cover" />
              ) : (
                <span className="text-gray-400 text-xs text-center px-1">No image</span>
              )}
            </div>
            <input
              className="input flex-1" type="file" accept="image/*"
              onChange={handleImageChange}
            />
          </div>
        </div>
      </div>

      <button
        onClick={() => add.mutate()}
        disabled={add.isPending || !form.fish_name || !form.category_id}
        className="mt-4 btn-primary w-full"
      >
        {add.isPending ? 'Adding…' : 'Add Stock'}
      </button>
    </div>
  )
}
