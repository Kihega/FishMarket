import { useQuery } from '@tanstack/react-query'
import { getSellers } from '../../api/sellers'
import SellerCard from '../../components/sellers/SellerCard'
import { useUIStore } from '../../store/uiStore'

export default function MarketPage() {
  const { openSignupChoice } = useUIStore()

  const { data, isLoading } = useQuery({
    queryKey: ['sellers-home'],
    queryFn: () => getSellers({}).then((r) => r.data),
  })

  return (
    <div>
      {/* HERO */}
      <section
        className="relative h-[90vh] flex items-center justify-center text-center text-white"
        style={{
          backgroundImage:
            'linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url(/hero-fish.jpg)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      >
        <div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">Fresh Fish from Water</h1>
          <p className="text-lg md:text-xl mb-6">
            Connecting Fishermen and Buyers Across Tanzania
          </p>
          <button
            onClick={openSignupChoice}
            className="bg-black hover:bg-gray-800 text-white px-8 py-3 rounded-lg font-semibold transition"
          >
            Get Started
          </button>
        </div>
      </section>

      {/* FEATURES */}
      <section className="flex flex-wrap justify-center gap-6 -mt-12 relative z-10 px-4">
        <FeatureCard icon="fa-fish" title="Fresh Catch" text="Daily fish supply from local fishermen" />
        <FeatureCard icon="fa-store" title="Market Access" text="Buyers connect directly with fishermen" />
        <FeatureCard icon="fa-truck" title="Fast Distribution" text="Efficient delivery and coordination" />
      </section>

      {/* MARKETPLACE — live sellers from the API */}
      <section className="text-center py-16 px-4">
        <h2 className="text-3xl font-bold text-blue-900 mb-2">Verified Sellers Near You</h2>
        <p className="text-gray-500 mb-10">Browse active fish sellers on the platform</p>

        {isLoading ? (
          <div className="flex flex-wrap justify-center gap-6">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="w-64 h-48 bg-gray-100 animate-pulse rounded-2xl" />
            ))}
          </div>
        ) : data?.data?.length ? (
          <div className="flex flex-wrap justify-center gap-6">
            {data.data.map((seller) => (
              <SellerCard key={seller.id} seller={seller} />
            ))}
          </div>
        ) : (
          <p className="text-gray-400">No active sellers yet — be the first to join!</p>
        )}
      </section>

      {/* ABOUT */}
      <section className="bg-blue-700 text-white text-center py-16 px-6">
        <h2 className="text-3xl font-bold mb-4">About the System</h2>
        <p className="max-w-2xl mx-auto leading-relaxed">
          This system is designed to improve fish market access and supply coordination
          in Tanzania. It connects fishermen directly with buyers, reduces middlemen, and
          ensures efficient distribution.
        </p>
      </section>

      {/* WHY CHOOSE US */}
      <section className="bg-gray-50 text-center py-16 px-4">
        <h2 className="text-3xl font-bold text-blue-900 mb-10">Why Choose Our System?</h2>
        <div className="flex flex-wrap justify-center gap-6">
          <FeatureCard icon="fa-bolt" title="Fast Access" text="Quick connection between fishermen and buyers" />
          <FeatureCard icon="fa-fish" title="Fresh Fish" text="Direct supply from local fishermen" />
          <FeatureCard icon="fa-check-circle" title="Reliable System" text="Efficient coordination and delivery" />
        </div>
      </section>

      {/* CONTACT */}
      <footer className="bg-gray-900 text-white text-center py-10 px-4">
        <h2 className="text-2xl font-bold mb-3">Contact Us</h2>
        <p>Email: fishmarket@gmail.com</p>
        <p>Phone: +255 710 491 613 / +255 616 421 613</p>
      </footer>
    </div>
  )
}

function FeatureCard({ icon, title, text }) {
  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 w-56 text-center hover:-translate-y-1 transition">
      <i className={`fas ${icon} text-3xl text-blue-600 mb-3`} />
      <h3 className="font-bold text-blue-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-500">{text}</p>
    </div>
  )
}
