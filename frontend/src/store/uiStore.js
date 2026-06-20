import { create } from 'zustand'

// Controls which auth modal (if any) is currently shown.
// modal: null | 'login' | 'signup-choice' | 'signup-seller' | 'signup-buyer'
export const useUIStore = create((set) => ({
  modal: null,
  sellerSignupStep: 1, // 1 = details, 2 = plan picker
  openLogin: () => set({ modal: 'login' }),
  openSignupChoice: () => set({ modal: 'signup-choice', sellerSignupStep: 1 }),
  openSignupSeller: () => set({ modal: 'signup-seller', sellerSignupStep: 1 }),
  openSignupBuyer: () => set({ modal: 'signup-buyer' }),
  nextSellerStep: () => set({ sellerSignupStep: 2 }),
  prevSellerStep: () => set({ sellerSignupStep: 1 }),
  closeModal: () => set({ modal: null, sellerSignupStep: 1 }),
}))
