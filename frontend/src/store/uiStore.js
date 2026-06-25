import { create } from 'zustand'

// Controls which auth modal (if any) is currently shown.
// modal: null | 'login' | 'signup-choice' | 'signup-seller' | 'signup-buyer'
export const useUIStore = create((set) => ({
  modal: null,
  openLogin: () => set({ modal: 'login' }),
  openSignupChoice: () => set({ modal: 'signup-choice' }),
  openSignupSeller: () => set({ modal: 'signup-seller' }),
  openSignupBuyer: () => set({ modal: 'signup-buyer' }),
  closeModal: () => set({ modal: null }),
}))
