"""Normalização de telefone para E.164 (+5511987654321).

Nunca monte "55{ddd}{phone}" na hora de gerar o link wa.me — normalize
uma vez, na gravação, e trate o campo já normalizado daí em diante
(MVP v6 §10/§17). Celular brasileiro tem 11 dígitos (DDD + 9 + 8 dígitos);
número antigo sem o 9 é aceito e corrigido.
"""

import re


class InvalidPhoneError(ValueError):
    pass


def normalize_br_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)

    # Remove código do país se já vier com ele.
    if digits.startswith("55") and len(digits) > 11:
        digits = digits[2:]

    if len(digits) == 10:
        # DDD (2) + número antigo sem o 9 (8 dígitos) — insere o 9.
        ddd, resto = digits[:2], digits[2:]
        digits = f"{ddd}9{resto}"
    elif len(digits) != 11:
        raise InvalidPhoneError(f"telefone inválido: {raw!r}")

    return f"+55{digits}"
