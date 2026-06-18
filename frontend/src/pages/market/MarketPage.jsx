import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getSellers } from '../../api/sellers'
import SellerCard from '../../components/sellers/SellerCard'

export default function MarketPage() {
  const [search, setSearch] = useState('')
  const { data, isLoading } = useQuery({
    queryKey: ['sellers', search],
    queryFn: () => getSellers({ location: search }).then(r => r.data),
  })

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-blue-900 mb-2">SmartFish Marketplace</h1>
      <p className="text-gray-500 mb-6">Browse verified fish sellers and their available stock</p>

      <input
        className="input max-w-sm mb-8"
        placeholder="Search by location…"
        value={search}
        onChange={e => setSearch(e.target.value)}
      />

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-48 bg-gray-200 animate-pulse rounded-2xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {data?.data?.map(seller => <SellerCard key={seller.id} seller={seller} />)}
        </div>
      )}
    </div>
  )
}
