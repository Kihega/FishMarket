#!/usr/bin/env python3
"""
PATCH v6 — SmartFish Frontend: Graceful Backend-Unreachable Handling
Run from project ROOT, on the `develop` branch.

ROOT CAUSE OF THE BLACK SCREEN:
  Render's free tier sleeps after ~15 min idle, and can be fully suspended.
  When MarketPage's first API call (getSellers) fails, nothing in the app
  caught that error — no error boundary, no fallback UI — so the page
  rendered nothing at all.

This patch adds:
  1. A React ErrorBoundary wrapping the whole app — catches ANY render
     crash and shows a friendly message instead of a black screen.
  2. A "Waking up the server..." retry state in MarketPage specifically
     for network/timeout failures (common with Render free tier cold starts,
     which can take 30-50 seconds on first request after sleep).
  3. A global axios timeout + retry-once-after-delay in client.js, since
     Render's cold start is slow but usually succeeds on a second attempt.

Run:
    cd FishMarket
    python3 patch_error_handling.py
"""

import os
import textwrap

ROOT = os.getcwd()
FRONTEND = os.path.join(ROOT, "frontend")

FILES = {}

# ── ErrorBoundary — catches any render-time crash app-wide ─────────────
FILES["src/components/ErrorBoundary.jsx"] = textwrap.dedent("""\
    import { Component } from 'react'

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
                <div className="text-5xl mb-4">⚠️</div>
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
""")

# ── api/client.js — add timeout so failed requests fail FAST and visibly ─
FILES["src/api/client.js"] = textwrap.dedent("""\
    import axios from 'axios'
    import { useAuthStore } from '../store/authStore'

    const client = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL,
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      // Render's free tier can take 30-50s to wake from sleep on the first
      // request. We give it generous room here rather than failing fast,
      // since a quick timeout would make cold starts look like real errors.
      timeout: 45000,
    })

    // Attach the Sanctum token to every outgoing request, if present.
    client.interceptors.request.use((config) => {
      const token = useAuthStore.getState().token
      if (token) config.headers.Authorization = `Bearer ${token}`
      return config
    })

    // If the backend ever returns 401 (expired/invalid token), clear local
    // auth state so the UI falls back to logged-out behavior instead of
    // silently failing every subsequent request.
    client.interceptors.response.use(
      (res) => res,
      (err) => {
        if (err.response?.status === 401) {
          useAuthStore.getState().clearAuth()
        }
        return Promise.reject(err)
      }
    )

    export default client
""")

# ── pages/market/MarketPage.jsx — add a "waking up" state for network errors ─
FILES["src/pages/market/MarketPage.jsx"] = textwrap.dedent("""\
    import { useQuery } from '@tanstack/react-query'
    import { getSellers } from '../../api/sellers'
    import SellerCard from '../../components/sellers/SellerCard'
    import { useUIStore } from '../../store/uiStore'

    export default function MarketPage() {
      const { openSignupChoice } = useUIStore()

      const { data, isLoading, isError, refetch, isFetching } = useQuery({
        queryKey: ['sellers-home'],
        queryFn: () => getSellers({}).then((r) => r.data),
        retry: 1,
        retryDelay: 3000,
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

            {isLoading || isFetching ? (
              <div>
                <div className="flex flex-wrap justify-center gap-6">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="w-64 h-48 bg-gray-100 animate-pulse rounded-2xl" />
                  ))}
                </div>
                <p className="text-gray-400 text-sm mt-4">
                  Connecting to server… this can take up to a minute if it's
                  waking up from sleep.
                </p>
              </div>
            ) : isError ? (
              <div className="max-w-md mx-auto bg-yellow-50 border border-yellow-200 rounded-xl p-6">
                <p className="text-yellow-800 font-medium mb-3">
                  Couldn't reach the server. It may be waking up — this can
                  take up to a minute on the free tier.
                </p>
                <button
                  onClick={() => refetch()}
                  className="bg-blue-700 hover:bg-blue-800 text-white px-5 py-2 rounded-lg font-semibold"
                >
                  Try Again
                </button>
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
""")

# ── main.jsx — wrap App in ErrorBoundary ────────────────────────────────
FILES["src/main.jsx"] = textwrap.dedent("""\
    import React from 'react'
    import ReactDOM from 'react-dom/client'
    import { BrowserRouter } from 'react-router-dom'
    import App from './App'
    import ErrorBoundary from './components/ErrorBoundary'
    import './index.css'

    ReactDOM.createRoot(document.getElementById('root')).render(
      <React.StrictMode>
        <ErrorBoundary>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </ErrorBoundary>
      </React.StrictMode>
    )
""")

def main():
    if not os.path.isdir(FRONTEND):
        print(f"❌  frontend/ folder not found at {FRONTEND}")
        print("    Run this script from your project ROOT (e.g. ~/FishMarket).")
        return

    for rel_path, content in FILES.items():
        full_path = os.path.join(FRONTEND, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📄  frontend/{rel_path}")

    print()
    print("✅  Error handling patch applied.")
    print("""
WHAT CHANGED
────────────
  • ErrorBoundary now wraps the entire app — any render crash shows a
    friendly retry screen instead of a black/blank page.
  • client.js now has a 45s timeout (Render cold starts can be slow).
  • MarketPage shows "waking up the server" + a retry button on failure,
    instead of silently failing.

NEXT STEPS
──────────
  1. Resume your Render service from the dashboard (you already found
     this — click "Resume" / "Restart").

  2. cd frontend && npm run build   (verify it still builds clean)

  3. Commit on develop:
       git add frontend/src/components/ErrorBoundary.jsx
       git add frontend/src/api/client.js
       git add frontend/src/pages/market/MarketPage.jsx
       git add frontend/src/main.jsx
       git commit -m "Fix: add error boundary + graceful backend-unreachable handling"
       git push origin develop

  4. Consider adding UptimeRobot (free) to ping your Render URL every
     10 minutes — this prevents the free-tier sleep entirely during
     your testing week, so this won't keep happening while you demo.
""")

if __name__ == "__main__":
    main()
