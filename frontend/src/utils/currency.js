/**
 * Formats a number as Tanzanian Shillings, e.g. formatTsh(15000) -> "Tsh 15,000.00"
 * Replaces the previous "TZS 15,000" (no decimals) format used inconsistently
 * across the app.
 */
export function formatTsh(amount) {
  const num = Number(amount) || 0
  return `Tsh ${num.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}
