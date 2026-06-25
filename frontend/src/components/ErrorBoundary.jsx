import { Component } from 'react'
import { AlertTriangle } from 'lucide-react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error, info) {
    // Logged for debugging — does not block the fallback UI below.
    console.error('SmartFish ErrorBoundary caught:', error, info)
  }

  handleRetry = () => {
    this.setState({ hasError: false })
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="text-center max-w-md">
            <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
            <h1 className="text-xl font-bold text-gray-800 mb-2">
              Something went wrong
            </h1>
            <p className="text-gray-500 mb-6">
              The app hit an unexpected error. This can happen if the
              backend server was asleep or unreachable. Try reloading —
              if it keeps happening, the backend may need attention.
            </p>
            <button
              onClick={this.handleRetry}
              className="bg-blue-700 hover:bg-blue-800 text-white font-semibold px-6 py-2.5 rounded-lg"
            >
              Reload Page
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
