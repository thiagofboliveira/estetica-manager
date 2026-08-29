import Decimal from "decimal.js";

/**
 * Espelha a config do backend (app/core/money.py): mesma precisão, mesmo
 * ROUND_HALF_UP. Se o backend mudar o arredondamento, mude AQUI e em
 * lugar nenhum mais — nunca duplique a config em outro arquivo.
 */
Decimal.set({
  precision: 28,
  rounding: Decimal.ROUND_HALF_UP,
  toExpNeg: -9,
  toExpPos: 21,
});

export { Decimal };
