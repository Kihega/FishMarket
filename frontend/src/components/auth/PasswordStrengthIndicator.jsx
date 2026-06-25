import { Check, X } from 'lucide-react'

/**
 * Live password strength checklist — shown while typing, matches the
 * backend's validation rule exactly: letters + numbers + special char,
 * minimum 8 characters.
 */
export function getPasswordChecks(password) {
  return {
    length: password.length >= 8,
    letter: /[a-zA-Z]/.test(password),
    number: /\d/.test(password),
    special: /[^a-zA-Z\d]/.test(password),
  }
}

export function isPasswordStrong(password) {
  const checks = getPasswordChecks(password)
  return Object.values(checks).every(Boolean)
}

export default function PasswordStrengthIndicator({ password }) {
  if (!password) return null

  const checks = getPasswordChecks(password)
  const rules = [
    { key: 'length', label: 'At least 8 characters' },
    { key: 'letter', label: 'Contains a letter' },
    { key: 'number', label: 'Contains a number' },
    { key: 'special', label: 'Contains a special character (!@#$ etc.)' },
  ]

  return (
    <div className="bg-gray-50 rounded-lg p-3 space-y-1 -mt-1">
      {rules.map((rule) => (
        <div
          key={rule.key}
          className={`flex items-center gap-2 text-xs ${
            checks[rule.key] ? 'text-green-600' : 'text-gray-400'
          }`}
        >
          {checks[rule.key] ? (
            <Check className="w-3.5 h-3.5 flex-shrink-0" />
          ) : (
            <X className="w-3.5 h-3.5 flex-shrink-0" />
          )}
          {rule.label}
        </div>
      ))}
    </div>
  )
}
