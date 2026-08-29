/**
 * Money — string decimal validada, branded para não ser confundida com
 * number. Ver ../../../ENGENHARIA.md invariante I1 e ENGENHARIA.md deste
 * projeto: a API manda dinheiro como STRING; se isto virasse number,
 * JSON.parse devolveria float64 e reintroduziria o erro que o backend
 * evita com Decimal.
 *
 * O front NUNCA recalcula lucro — o backend manda o valor pronto. Este
 * módulo serve para somas de exibição (totalizar um carrinho, ordenar
 * por valor) e para o input de moeda, não para reimplementar a fórmula.
 */

import { Decimal } from "./decimal-config";

declare const MoneyBrand: unique symbol;
export type Money = string & { readonly [MoneyBrand]: "BRL" };

declare const RateBrand: unique symbol;
export type Rate = string & { readonly [RateBrand]: true };

const MONEY_RE = /^-?\d+(\.\d{1,2})?$/;

/** Única porta de entrada — valida o formato que o backend promete. */
export function money(raw: string): Money {
  if (!MONEY_RE.test(raw)) {
    throw new TypeError(`Valor monetário inválido vindo da API: ${JSON.stringify(raw)}`);
  }
  return raw as Money;
}

/** Versão que não explode — para dados de terceiros / campos opcionais. */
export function tryMoney(raw: unknown): Money | null {
  return typeof raw === "string" && MONEY_RE.test(raw) ? (raw as Money) : null;
}

export const ZERO = "0.00" as Money;

const d = (m: Money) => new Decimal(m);
const out = (x: Decimal): Money => x.toFixed(2) as Money;

export const add = (a: Money, b: Money): Money => out(d(a).plus(d(b)));
export const sub = (a: Money, b: Money): Money => out(d(a).minus(d(b)));

export const sum = (xs: readonly Money[]): Money =>
  out(xs.reduce((acc, m) => acc.plus(d(m)), new Decimal(0)));

/** Multiplicação por QUANTIDADE (inteiro), não por outro Money. */
export const mulQty = (a: Money, qty: number): Money => {
  if (!Number.isInteger(qty)) throw new TypeError("qty deve ser inteiro");
  return out(d(a).times(qty));
};

/** Aplicação de taxa — Rate, não number, para não passar 40 no lugar de 0.40. */
export const applyRate = (a: Money, r: Rate): Money => out(d(a).times(new Decimal(r)));

export const isNegative = (a: Money): boolean => d(a).isNegative();
export const isZero = (a: Money): boolean => d(a).isZero();

/**
 * Comparação numérica. NUNCA use sort() padrão em Money:
 * ["9.00", "10.00"].sort() === ["10.00", "9.00"] — ordem lexicográfica.
 * Use [a, b].sort((x, y) => cmp(x, y)).
 */
export const cmp = (a: Money, b: Money): -1 | 0 | 1 => d(a).comparedTo(d(b)) as -1 | 0 | 1;
