import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

// Auth state is persisted to sessionStorage (not localStorage) so the
// session doesn't outlive the browser tab/window — closing the browser
// requires a fresh login next time, instead of staying signed in
// indefinitely. The backend already deletes the access token on
// /logout; this just stops the frontend from keeping an old token
// around for "a long time" beyond the current browsing session.
export const useAuthStore = create(
  persist(
    (set) => ({
      user: null,
      token: null,
      setAuth: (user, token) => set({ user, token }),
      clearAuth: () => set({ user: null, token: null }),
    }),
    {
      name: 'fish-market-auth',
      storage: createJSONStorage(() => sessionStorage),
    }
  )
)
