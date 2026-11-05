/**
 * Formats a 0-1 probability as a whole-number percentage. Tiny values read
 * "<1%" rather than 0%, and near-certain ones ">99%" rather than 100%: softmax
 * saturates even on predictions that are wrong, so the UI never claims certainty.
 */
export function formatPercent(value: number, locale: string): string {
  const formatter = new Intl.NumberFormat(locale, { style: "percent", maximumFractionDigits: 0 });
  if (value > 0 && value < 0.01) return `<${formatter.format(0.01)}`;
  if (value >= 0.995) return `>${formatter.format(0.99)}`;
  return formatter.format(value);
}
