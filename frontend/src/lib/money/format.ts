import type { Money, Rate } from "./money";

/**
 * Intl.NumberFormat.format() aceita string desde ES2023 e a trata como
 * decimal exato, mas os tipos do TS ainda não refletem essa assinatura
 * (lib.es2023 do TS não inclui o overload de string). O cast aqui é
 * documentado e único — nunca espalhe `as unknown as string` pelo código,
 * sempre passe pelos formatters deste arquivo.
 */
type NumberFormatWithStringInput = {
  format: (value: string) => string;
};

function asStringFormatter(nf: Intl.NumberFormat): NumberFormatWithStringInput {
  return nf as unknown as NumberFormatWithStringInput;
}

// Instanciar uma vez: criar NumberFormat em render é ~100x mais lento.
const BRL = asStringFormatter(
  new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }),
);

/**
 * format(string) — o Intl parseia o decimal direto, sem float
 * intermediário. NUNCA troque por format(Number(m)): reintroduz float64.
 */
export function formatBRL(m: Money): string {
  return BRL.format(m);
}

/** Compacto para o dashboard no celular: R$ 12,4 mil. */
const BRL_COMPACT = asStringFormatter(
  new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    notation: "compact",
    maximumFractionDigits: 1,
  }),
);
export const formatBRLCompact = (m: Money) => BRL_COMPACT.format(m);

/** Só os dígitos, para exibição sem "R$". */
const PLAIN = asStringFormatter(
  new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }),
);
export const formatPlain = (m: Money) => PLAIN.format(m);

const PCT = asStringFormatter(
  new Intl.NumberFormat("pt-BR", { style: "percent", maximumFractionDigits: 2 }),
);
export const formatRate = (r: Rate) => PCT.format(r);

/**
 * Fallback manual, caso precise suportar navegador sem
 * Intl.NumberFormat.format(string) (ES2023+). Nunca passe por Number().
 */
export function formatBRLFallback(m: Money): string {
  const neg = m.startsWith("-");
  const [int, dec = "00"] = (neg ? m.slice(1) : m).split(".");
  const grouped = int.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `${neg ? "-" : ""}R$ ${grouped},${dec.padEnd(2, "0")}`;
}
