import { Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from './store/authStore'
import Layout from './components/layout/Layout'
import AuthModalRoot from './components/auth/AuthModalRoot'
import MarketPage from './pages/market/MarketPage'
import SellerPage from './pages/market/SellerPage'
import SellerDashboard from './pages/dashboard/SellerDashboard'
import BuyerDashboard from './pages/dashboard/BuyerDashboard'
import AdminPanel from './pages/admin/AdminPanel'

const qc = new QueryClient()

function PrivateRoute({ children, roles }) {
  const { user } = useAuthStore()
  if (!user) return <Navigate to="/" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />
  return children
}

export default function App() {
  const { user } = useAuthStore()
  return (
    <QueryClientProvider client={qc}>
      <Toaster position="top-right" />
      <AuthModalRoot />
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<MarketPage />} />
          <Route path="/sellers/:id" element={<SellerPage />} />
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                {user?.role === 'seller' ? <SellerDashboard /> : <BuyerDashboard />}
              </PrivateRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <PrivateRoute roles={['admin']}>
                <AdminPanel />
              </PrivateRoute>
            }
          />
        </Route>
      </Routes>
    </QueryClientProvider>
  )
}
