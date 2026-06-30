/**
 * Capitalizes each word as the user types (e.g. "john peter mwasege" ->
 * "John Peter Mwasege"), so a full name made up of multiple parts
 * (first / middle / last) always displays in proper case live in the
 * form, not just after the backend corrects it on submit.
 * Keeps a single trailing space so typing a new word doesn't fight
 * the cursor.
 */
export function toTitleCase(value) {
  return value.replace(/\b\p{L}/gu, (ch) => ch.toUpperCase())
}

/**
 * Tanzanian phone numbers entered here are always stored as
 * +255 followed by exactly 9 digits (e.g. +255712345678 — 12
 * characters after the +). This strips anything that isn't a digit
 * after the fixed +255 prefix and hard-caps it at 9 digits so the
 * field can never grow longer than a valid number, while still
 * letting the user freely edit/backspace within those 9 digits.
 */
export function formatTzPhone(value) {
  const digitsOnly = value.replace(/^\+255/, '').replace(/\D/g, '').slice(0, 9)
  return `+255${digitsOnly}`
}

/** True once the phone has the full +255 plus exactly 9 digits. */
export function isCompleteTzPhone(value) {
  return /^\+255\d{9}$/.test(value)
}
