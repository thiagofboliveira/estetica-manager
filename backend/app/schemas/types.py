"""Tipos Pydantic compartilhados entre schemas.

MoneyOut serializa Decimal como STRING no JSON — nunca número. O front
consome com decimal.js/centavos; se isto virasse número, JSON.parse
devolveria float64 e reintroduziria o erro que o backend evita com
Decimal (ver ../../ENGENHARIA.md invariante I1). Decisão marcada como
NÃO retrofitável: mudar depois quebra todo consumidor da API.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated

from pydantic import BeforeValidator, PlainSerializer


def _to_decimal(v: object) -> Decimal:
    if isinstance(v, float):
        # Um float chegando aqui já perdeu precisão antes de qualquer
        # cálculo nosso — falhar alto é melhor que persistir
        # 10.999999999999998.
        raise ValueError('envie valores monetários como string: "10.50"')
    return Decimal(str(v))


MoneyOut = Annotated[
    Decimal,
    BeforeValidator(_to_decimal),
    PlainSerializer(
        lambda d: str(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        return_type=str,
        when_used="json",  # em Python continua Decimal para cálculo/teste
    ),
]

# RateOut: mesma lógica do MoneyOut (Decimal -> string no JSON), mas com
# 4 casas — para taxas/margens (Numeric(5,4) ou Numeric(9,4)), nunca para
# dinheiro. Duas casas arredondariam a taxa antes de qualquer uso
# (backend/ENGENHARIA.md §3).
RateOut = Annotated[
    Decimal,
    BeforeValidator(_to_decimal),
    PlainSerializer(
        lambda d: str(d.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)),
        return_type=str,
        when_used="json",
    ),
]
