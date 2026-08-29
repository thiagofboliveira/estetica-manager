/**
 * PROTÓTIPO — F-014. Cálculo de lucro ilustrativo, feito no cliente,
 * só para dar sensação de produto ao protótipo de venda avulsa.
 *
 * Isto NÃO é o motor de lucro real (MVP v6 §12, TASK-018): não lê
 * `financial_settings`/`payment_fee_rules` da conta, usa taxas de
 * mercado fixas como chute. Quando T-015/T-018 existirem, a tela real
 * troca isto por `lucro_real` vindo pronto da API — o front nunca
 * recalcula lucro (ENGENHARIA.md invariante).
 */

import { ZERO, applyRate, mulQty, sub, sum, type Money, type Rate } from "@/lib/money/money";
import { Decimal } from "@/lib/money/decimal-config";

export type PaymentMethod = "PIX" | "CARD";

// Chute de mercado só para o protótipo parecer real — não é dado da conta.
const CARD_FEE_RATE = "0.0499" as Rate;
const PIX_FEE_RATE = "0" as Rate;

export function estimateFee(total: Money, method: PaymentMethod): Money {
  return applyRate(total, method === "CARD" ? CARD_FEE_RATE : PIX_FEE_RATE);
}

export function estimateProfit(params: {
  unitPrice: Money;
  unitCost: Money;
  paymentMethod: PaymentMethod;
}): { total: Money; fee: Money; cost: Money; profit: Money } {
  const total = params.unitPrice;
  const cost = params.unitCost || ZERO;
  const fee = estimateFee(total, params.paymentMethod);
  const profit = sub(sub(total, fee), cost);
  return { total, fee, cost, profit };
}

export type PackageLine = {
  unitPrice: Money;
  unitCost: Money;
  quantity: number;
};

/**
 * Rateio do desconto por item, proporcional a unit_price × quantity
 * (MVP v6 §11.5). Largest remainder: o último item absorve o centavo
 * de arredondamento, para o rateio fechar exatamente com o total —
 * mesmo princípio de `app/core/money.py::allocate()` no backend, mas
 * reimplementado aqui só para a exibição do protótipo (nunca é o valor
 * gravado; a venda real faz esse rateio no servidor, TASK-018).
 */
function allocateDiscount(lineTotals: Money[], discount: Money): Money[] {
  const grandTotal = sum(lineTotals);
  if (new Decimal(grandTotal).isZero()) return lineTotals.map(() => ZERO);

  const shares = lineTotals.map((t) =>
    new Decimal(discount).times(new Decimal(t)).dividedBy(new Decimal(grandTotal)).toDecimalPlaces(2),
  );
  const allocated = shares.reduce((acc, s) => acc.plus(s), new Decimal(0));
  const remainder = new Decimal(discount).minus(allocated);
  if (shares.length > 0) {
    shares[shares.length - 1] = shares[shares.length - 1].plus(remainder);
  }
  return shares.map((s) => s.toFixed(2) as Money);
}

export function estimatePackageProfit(params: {
  lines: PackageLine[];
  discount: Money;
  paymentMethod: PaymentMethod;
}): {
  itemsTotal: Money;
  discount: Money;
  grossAmount: Money;
  fee: Money;
  cost: Money;
  profit: Money;
} {
  const lineTotals = params.lines.map((l) => mulQty(l.unitPrice, l.quantity));
  const itemsTotal = sum(lineTotals.length ? lineTotals : [ZERO]);
  const discount = params.discount || ZERO;
  const grossAmount = sub(itemsTotal, discount);
  const fee = estimateFee(grossAmount, params.paymentMethod);
  const cost = sum(
    params.lines.length ? params.lines.map((l) => mulQty(l.unitCost || ZERO, l.quantity)) : [ZERO],
  );
  const profit = sub(sub(grossAmount, fee), cost);
  return { itemsTotal, discount, grossAmount, fee, cost, profit };
}

export const allocateDiscountForDisplay = allocateDiscount;
