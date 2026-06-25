import { Link, useNavigate } from 'react-router-dom'
import { Fish } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import { useUIStore } from '../../store/uiStore'
import { logout } from '../../api/auth'

export default function Navbar() {
  const { user, clearAuth } = useAuthStore()
  const { openLogin, openSignupChoice } = useUIStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout().catch(() => {})
    clearAuth()
    navigate('/')
  }

  return (
    <header className="flex justify-between items-center px-8 py-4 bg-blue-700 text-white sticky top-0 z-40 shadow">
      <Link to="/" className="text-xl font-bold flex items-center gap-2">
        <Fish className="w-6 h-6" /> SmartFish
      </Link>

      <nav className="flex items-center gap-6">
        <Link to="/" className="hover:text-blue-200 font-medium">Home</Link>

        {user ? (
          <>
            <Link to="/dashboard" className="hover:text-blue-200 font-medium">Dashboard</Link>
            {user.role === 'admin' && (
              <Link to="/admin" className="hover:text-blue-200 font-medium">Admin</Link>
            )}
            <button
              onClick={handleLogout}
              className="bg-white text-blue-700 font-semibold px-4 py-1.5 rounded-lg hover:bg-blue-50"
            >
              Logout
            </button>
          </>
        ) : (
          <>
            <button onClick={openLogin} className="hover:text-blue-200 font-medium">
              Login
            </button>
            <button
              onClick={openSignupChoice}
              className="bg-white text-blue-700 font-semibold px-4 py-1.5 rounded-lg hover:bg-blue-50"
            >
              Sign Up
            </button>
          </>
        )}
      </nav>
    </header>
  )
}
