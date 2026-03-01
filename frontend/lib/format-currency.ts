/**
 * PT-BR currency formatter with abbreviated large values.
 * SAB-012 AC4: "R$ 3,5 bi", "R$ 130,7 mi", "R$ 45.000"
 */
export function formatCurrencyBR(value: number): string {
  if (value >= 1_000_000_000) {
    const bi = value / 1_000_000_000;
    return `R$ ${bi.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} bi`;
  }
  if (value >= 1_000_000) {
    const mi = value / 1_000_000;
    return `R$ ${mi.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} mi`;
  }
  // Intl.NumberFormat uses non-breaking space (\u00A0) — normalize to regular space
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value).replace(/\u00A0/g, " ");
}
