import { Link } from 'react-router-dom'
import { Fish, MapPin } from 'lucide-react'

export default function SellerCard({ seller }) {
  return (
    <div className="bg-white rounded-2xl shadow p-5 hover:shadow-md transition flex flex-col gap-3">
      <div className="flex items-center gap-3">
        {seller.brand_logo
          ? <img
              src={seller.brand_logo.startsWith('data:') ? seller.brand_logo : `/storage/${seller.brand_logo}`}
              alt={seller.name}
              className="w-14 h-14 rounded-full object-cover border"
            />
          : <div className="w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center">
              <Fish className="w-6 h-6 text-blue-600" />
            </div>
        }
        <div>
          <h3 className="font-bold text-blue-900 text-lg">{seller.name}</h3>
          <p className="text-gray-500 text-sm flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5" /> {seller.location_address || seller.location}
          </p>
        </div>
      </div>
      <p className="text-gray-600 text-sm">{seller.office_address}</p>
      <div className="flex items-center justify-between mt-auto">
        <span className="text-sm text-blue-600">{seller.fish_stocks_count} items</span>
        <Link to={`/sellers/${seller.id}`}
          className="bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-blue-700">
          View Shop
        </Link>
      </div>
    </div>
  )
}
