import { Link } from 'react-router-dom'
import { Fish } from 'lucide-react'
import BackButton from './BackButton'

// Top bar is now branding-only. Home / Dashboard / Logout / Login / Sign Up
// buttons were removed from here on every page (including all dashboards)
// — each dashboard already has its own sidebar with Home + Logout, and the
// public homepage has its own "Get Started" CTA, so this bar no longer
// needs to duplicate that navigation.
export default function Navbar() {
  return (
    <header className="flex justify-between items-center px-8 py-4 bg-blue-700 text-white sticky top-0 z-40 shadow">
      <div className="flex items-center">
        <BackButton />
        <Link to="/" className="text-xl font-bold flex items-center gap-2">
          <Fish className="w-6 h-6" /> SmartFish
        </Link>
      </div>
    </header>
  )
}
