import { useNavigate, useLocation } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'

// Global in-app "Back" button. Shown on every page except the home
// page. Uses browser history when the user actually navigated here
// from somewhere inside the app (location.key !== 'default'); falls
// back to the home page when the page was opened directly (e.g. a
// refresh or a bookmarked/deep link), since there's no in-app history
// to go back to in that case.
export default function BackButton() {
  const navigate = useNavigate()
  const location = useLocation()

  if (location.pathname === '/') return null

  const handleBack = () => {
    if (location.key !== 'default') {
      navigate(-1)
    } else {
      navigate('/')
    }
  }

  return (
    <button
      onClick={handleBack}
      aria-label="Go back"
      className="flex items-center gap-1.5 text-white/90 hover:text-white transition text-sm font-medium mr-4"
    >
      <ArrowLeft className="w-5 h-5" />
      <span className="hidden sm:inline">Back</span>
    </button>
  )
}
