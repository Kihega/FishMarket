import ModalShell from './ModalShell'
import { useUIStore } from '../../store/uiStore'

export default function SignupChoiceModal() {
  const { closeModal, openSignupSeller, openSignupBuyer, openLogin } = useUIStore()

  return (
    <ModalShell onClose={closeModal}>
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-blue-900">Join FishMarket TZ</h2>
        <p className="text-gray-500 mt-1">Choose how you want to use the platform</p>
      </div>

      <div className="grid gap-4">
        <button
          onClick={openSignupSeller}
          className="border-2 border-blue-600 rounded-xl p-5 text-left hover:bg-blue-50 transition group"
        >
          <div className="flex items-center gap-3">
            <span className="text-3xl">🐟</span>
            <div>
              <h3 className="font-bold text-blue-900 group-hover:text-blue-700">
                Create Seller Account
              </h3>
              <p className="text-sm text-gray-500">
                List your fish stock and reach buyers directly
              </p>
            </div>
          </div>
        </button>

        <button
          onClick={openSignupBuyer}
          className="border-2 border-blue-600 rounded-xl p-5 text-left hover:bg-blue-50 transition group"
        >
          <div className="flex items-center gap-3">
            <span className="text-3xl">🛒</span>
            <div>
              <h3 className="font-bold text-blue-900 group-hover:text-blue-700">
                Create Buyer Account
              </h3>
              <p className="text-sm text-gray-500">
                Browse sellers and order fresh fish
              </p>
            </div>
          </div>
        </button>
      </div>

      <p className="text-center text-sm text-gray-500 mt-6">
        Already have an account?{' '}
        <button onClick={openLogin} className="text-blue-700 font-semibold hover:underline">
          Log in
        </button>
      </p>
    </ModalShell>
  )
}
