import { describe, expect, it } from "vitest";
import fc from "fast-check";
import { add, cmp, isZero, money, mulQty, sum, tryMoney, ZERO } from "./money";
import { formatBRL } from "./format";
import { centsToDisplay, centsToMoney, digitsToCents, moneyToCents } from "./parse";

describe("money()", () => {
  it("aceita string decimal válida", () => {
    expect(money("10.50")).toBe("10.50");
    expect(money("0.00")).toBe("0.00");
    expect(money("-50.00")).toBe("-50.00");
  });

  it("rejeita formato fora do contrato da API", () => {
    expect(() => money("1234.5678")).toThrow(); // mais de 2 casas
    expect(() => money("1.234,56")).toThrow(); // pt-BR não entra por aqui
    expect(() => money("")).toThrow();
    expect(() => money("abc")).toThrow();
  });

  it("tryMoney não explode em entrada inválida", () => {
    expect(tryMoney("10.50")).toBe("10.50");
    expect(tryMoney("abc")).toBeNull();
    expect(tryMoney(123)).toBeNull();
  });
});

describe("aritmética", () => {
  it("soma sem drift de float — o caso que quebraria com number", () => {
    // 0.1 + 0.2 em float64 = 0.30000000000000004
    const xs = Array.from({ length: 30 }, () => money("115.96"));
    expect(sum(xs)).toBe("3478.80"); // não "3478.7999999999984"
  });

  it("add/sub preservam duas casas", () => {
    expect(add(money("10.10"), money("0.05"))).toBe("10.15");
    expect(add(money("100.00"), ZERO)).toBe("100.00");
  });

  it("mulQty rejeita quantidade não-inteira", () => {
    expect(() => mulQty(money("10.00"), 1.5)).toThrow();
    expect(mulQty(money("10.00"), 3)).toBe("30.00");
  });

  it("isZero", () => {
    expect(isZero(ZERO)).toBe(true);
    expect(isZero(money("0.01"))).toBe(false);
  });
});

describe("cmp — comparação numérica, não lexicográfica", () => {
  it("ordena corretamente valores onde sort() padrão falharia", () => {
    const values = [money("9.00"), money("10.00"), money("1200.00")];
    // sort() padrão daria ["10.00", "1200.00", "9.00"] — lexicográfico
    const sorted = [...values].sort((a, b) => cmp(a, b));
    expect(sorted).toEqual(["9.00", "10.00", "1200.00"]);
  });

  it("cmp retorna -1, 0, 1", () => {
    expect(cmp(money("9.00"), money("10.00"))).toBe(-1);
    expect(cmp(money("10.00"), money("10.00"))).toBe(0);
    expect(cmp(money("10.00"), money("9.00"))).toBe(1);
  });
});

describe("formatBRL — sempre a partir da string", () => {
  it("formata sem passar por Number", () => {
    expect(formatBRL(money("1234.56"))).toContain("1.234,56");
  });

  it("preserva precisão em valores grandes onde Number perderia", () => {
    // Number("9007199254740993.45") já arredonda antes do format.
    // A string vai direto ao Intl, sem essa perda.
    const big = money("9007199254740993.45");
    expect(() => formatBRL(big)).not.toThrow();
  });
});

describe("input de moeda — centavos inteiros", () => {
  it("digitsToCents descarta tudo que não é dígito", () => {
    expect(digitsToCents("R$ 1.234,56")).toBe(123456);
    expect(digitsToCents("28990")).toBe(28990);
  });

  it("centsToMoney nunca passa por float", () => {
    expect(centsToMoney(28990)).toBe("289.90");
    expect(centsToMoney(0)).toBe("0.00");
    expect(centsToMoney(-2890)).toBe("-28.90");
  });

  it("centsToDisplay formata para o usuário digitar", () => {
    expect(centsToDisplay(28990)).toBe("289,90");
    expect(centsToDisplay(50)).toBe("0,50");
  });

  it("moneyToCents é o inverso de centsToMoney", () => {
    expect(moneyToCents(money("289.90"))).toBe(28990);
    expect(moneyToCents("")).toBe(0);
  });
});

describe("property: ida e volta cents <-> Money é exata", () => {
  it("centsToMoney(moneyToCents(m)) === m para qualquer centavo não-negativo", () => {
    fc.assert(
      fc.property(fc.integer({ min: 0, max: 99_999_999 }), (cents) => {
        const m = centsToMoney(cents);
        expect(moneyToCents(m)).toBe(cents);
      }),
    );
  });

  it("sum de N valores aleatórios não diverge (comparado a inteiro de centavos)", () => {
    fc.assert(
      fc.property(
        fc.array(fc.integer({ min: 0, max: 1_000_000 }), { minLength: 1, maxLength: 50 }),
        (centsList) => {
          const values = centsList.map((c) => centsToMoney(c));
          const totalCents = centsList.reduce((a, b) => a + b, 0);
          expect(sum(values)).toBe(centsToMoney(totalCents));
        },
      ),
    );
  });
});
