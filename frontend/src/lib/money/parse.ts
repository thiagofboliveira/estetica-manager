import type { Money } from "./money";

/** Teto de sanity para procedimento de estética: R$ 999.999,99. */
const MAX_CENTS = 99_999_999;

/** "289.90" -> 28990 */
export function moneyToCents(m: Money | ""): number {
  if (!m) return 0;
  const [i, d = "0"] = m.split(".");
  return Number(i) * 100 + Number(d.padEnd(2, "0").slice(0, 2));
}

/** 28990 -> "289.90" (exato: nunca passa por float) */
export function centsToMoney(c: number): Money {
  const neg = c < 0;
  const abs = Math.abs(c);
  return `${neg ? "-" : ""}${Math.floor(abs / 100)}.${String(abs % 100).padStart(2, "0")}` as Money;
}

/** 28990 -> "289,90" para exibir no input de máscara. */
export function centsToDisplay(c: number): string {
  const s = String(Math.abs(c)).padStart(3, "0");
  const int = s.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `${c < 0 ? "-" : ""}${int},${s.slice(-2)}`;
}

/** Descarta tudo que não é dígito: colar "R$ 1.234,56" vira 123456 centavos. */
export function digitsToCents(raw: string): number {
  const digits = raw.replace(/\D/g, "").slice(0, 9);
  return Math.min(digits ? Number.parseInt(digits, 10) : 0, MAX_CENTS);
}
