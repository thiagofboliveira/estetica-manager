"""Aritmética monetária. Núcleo do produto — sem banco, sem I/O.

Regras (ver ../../ENGENHARIA.md, invariante I1):
  - Dinheiro nunca é float. Só Decimal.
  - Arredondamento é ROUND_HALF_UP (não o banker's rounding, que é o
    default do Python) — é a expectativa contábil brasileira.
  - Arredonda-se só na fronteira (persistência/serialização); a cadeia
    de cálculo mantém precisão total.
"""

from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal, InvalidOperation

CENTS = Decimal("0.01")
ZERO = Decimal("0.00")


def money(value: Decimal | int | str) -> Decimal:
    """Normaliza para Decimal com 2 casas, ROUND_HALF_UP.

    float é proibido: Decimal(0.1) != Decimal("0.1") — o float já chegou
    com erro de representação binária antes de qualquer cálculo.
    """
    if isinstance(value, float):
        raise TypeError(
            "float é proibido em cálculo monetário — use Decimal('10.50') ou str"
        )
    try:
        return Decimal(value).quantize(CENTS, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError(f"valor monetário inválido: {value!r}") from exc


def apply_rate(base: Decimal, rate: Decimal) -> Decimal:
    """base * rate, arredondado uma única vez no fim."""
    return money(base * rate)


def allocate(total: Decimal, weights: list[Decimal]) -> list[Decimal]:
    """Rateia `total` entre N parcelas proporcionalmente a `weights`.

    Garante sum(resultado) == total EXATAMENTE — largest remainder (Hare
    quota), não "o último item absorve o resto": esse método ingênuo
    concentra o desvio inteiro num único item (com 10 itens e R$ 0,09 de
    sobra, o último fica 9 centavos fora da proporção — pior ainda se
    esse item for depois estornado). Largest remainder espalha no máximo
    1 centavo por item.

    Funciona para total positivo (desconto) ou negativo (estorno) —
    ROUND_DOWN trunca em direção a zero e o resto é redistribuído com o
    mesmo sinal.
    """
    if not weights:
        return []

    total = money(total)
    total_weight = sum(weights)

    if total_weight == 0:
        # Todos os pesos zero (ex: venda 100% cortesia) — divide igualmente
        # para não dividir por zero.
        weights = [Decimal(1)] * len(weights)
        total_weight = Decimal(len(weights))

    sign = Decimal(-1) if total < 0 else Decimal(1)
    abs_total = abs(total)

    exact = [abs_total * w / total_weight for w in weights]
    floors = [e.quantize(CENTS, rounding=ROUND_DOWN) for e in exact]

    remainder_cents = int(((abs_total - sum(floors)) / CENTS).to_integral_value())

    # Desempate por índice (-i) mantém determinístico: um recálculo
    # reproduz exatamente o mesmo rateio.
    order = sorted(
        range(len(weights)),
        key=lambda i: (exact[i] - floors[i], -i),
        reverse=True,
    )
    for i in order[:remainder_cents]:
        floors[i] += CENTS

    result = [f * sign for f in floors]

    assert sum(result) == total, f"rateio não fechou: {sum(result)} != {total}"
    return result
