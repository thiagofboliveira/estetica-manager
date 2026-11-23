"""Checagem de números: a IA não pode inventar valor.

Todo número que aparece no texto gerado precisa existir no payload que o
backend entregou. Se aparecer um número que não veio dos dados, o texto é
descartado e vale o texto fixo. É o que garante "número errado é pior que
nenhum" mesmo quando o modelo erra.
"""

import re

_NUMBER = re.compile(r"\d[\d.,]*")


def _canon(token: str) -> str:
    """Compara só os dígitos: "1.234,50" e "1234.50" viram "123450"."""
    digits = re.sub(r"\D", "", token)
    return digits.lstrip("0") or "0"


def numbers_in(text: str) -> set[str]:
    return {_canon(m) for m in _NUMBER.findall(text)}


def allowed_numbers(*values: object) -> set[str]:
    """Números permitidos, extraídos dos valores do payload (str, int, Decimal)."""
    allowed: set[str] = set()
    for v in values:
        allowed |= numbers_in(str(v))
    return allowed


def is_grounded(text: str, allowed: set[str]) -> bool:
    """True se todo número do texto estiver entre os permitidos."""
    return numbers_in(text) <= allowed
