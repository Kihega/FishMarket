import { useUIStore } from '../../store/uiStore'
import LoginModal from './LoginModal'
import SignupChoiceModal from './SignupChoiceModal'
import SellerSignupModal from './SellerSignupModal'
import BuyerSignupModal from './BuyerSignupModal'

export default function AuthModalRoot() {
  const { modal } = useUIStore()

  if (modal === 'login') return <LoginModal />
  if (modal === 'signup-choice') return <SignupChoiceModal />
  if (modal === 'signup-seller') return <SellerSignupModal />
  if (modal === 'signup-buyer') return <BuyerSignupModal />
  return null
}
