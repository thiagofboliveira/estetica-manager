"""Mapeamento de colunas de planilha de pacientes (AI-08).

A IA SÓ sugere qual coluna é qual campo. Quem converte, valida e importa é o
código de sempre (``PatientService.batch_import``). Para a IA nunca vai dado de
paciente: só os cabeçalhos e, por coluna, poucos exemplos MASCARADOS (letras e
dígitos trocados por a/A/9), que mostram o formato sem revelar a pessoa.
"""

import json
import re
import unicodedata
from typing import Final

FIELDS: Final[tuple[str, ...]] = ("name", "phone", "email", "notes", "last_visit_date")
MAX_COLUMNS: Final = 50
MAX_SAMPLE_ROWS: Final = 5

SYSTEM_PROMPT = (
    "Você mapeia colunas de uma planilha de pacientes de uma clínica de estética. "
    "Receba os cabeçalhos e exemplos mascarados (letras viram a/A e dígitos viram 9) "
    "e diga qual coluna corresponde a cada campo: name (nome da paciente), phone "
    "(telefone ou WhatsApp), email, notes (observações) e last_visit_date (data da "
    'última visita). Responda SOMENTE com JSON no formato {"name": 0, "phone": 2, '
    '"email": null, "notes": null, "last_visit_date": null}, usando o número da '
    "coluna (começando em 0) ou null quando não existir. Não repita colunas."
)

_HEURISTICS: Final[dict[str, re.Pattern[str]]] = {
    "name": re.compile(r"\b(nome|name|paciente|cliente|patient)\b"),
    "phone": re.compile(
        r"\b(telefone|celular|whats\w*|fone|tel|phone|contato|numero|mobile)\b"
    ),
    "email": re.compile(r"\b(e-?mail|email)\b"),
    "notes": re.compile(r"\b(obs\w*|anotac\w*|notas?|notes?|historico|comentario\w*)\b"),
    "last_visit_date": re.compile(
        r"\b(ultima\s+(visita|consulta|sessao|atendimento)|last\s+visit|ultimo\s+atendimento)\b"
    ),
}


def _norm(text: str) -> str:
    base = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", base.lower()).strip()


def heuristic_mapping(headers: list[str]) -> dict[str, int | None]:
    """Mapeamento por nome do cabeçalho. Cada coluna vai para no máximo um campo;
    a primeira coluna que combina com o campo vence."""
    mapping: dict[str, int | None] = dict.fromkeys(FIELDS)
    used: set[int] = set()
    # Campos mais específicos primeiro, para "ultima visita" não virar "name".
    for field in ("last_visit_date", "email", "phone", "notes", "name"):
        pattern = _HEURISTICS[field]
        for idx, header in enumerate(headers):
            if idx in used:
                continue
            if pattern.search(_norm(header)):
                mapping[field] = idx
                used.add(idx)
                break
    return mapping


def is_confident(mapping: dict[str, int | None]) -> bool:
    """Nome e telefone achados pelos cabeçalhos dispensam a IA."""
    return mapping.get("name") is not None and mapping.get("phone") is not None


def mask_value(value: str, limit: int = 40) -> str:
    """Letras viram a/A, dígitos viram 9; pontuação fica. Mostra o formato, não a pessoa."""
    out = []
    for ch in value.strip()[:limit]:
        if ch.isdigit():
            out.append("9")
        elif ch.isalpha():
            out.append("A" if ch.isupper() else "a")
        else:
            out.append(ch)
    return "".join(out)


def build_user_prompt(headers: list[str], sample_rows: list[list[str]]) -> str:
    cols = []
    for idx, header in enumerate(headers):
        exemplos = [
            mask_value(row[idx])
            for row in sample_rows[:MAX_SAMPLE_ROWS]
            if idx < len(row) and row[idx].strip()
        ]
        cols.append(f"{idx}: cabeçalho={header.strip()[:60]!r} exemplos={exemplos}")
    return "Colunas:\n" + "\n".join(cols) + "\nResponda só o JSON."


def parse_ai_mapping(text: str | None, n_columns: int) -> dict[str, int | None] | None:
    """Valida a resposta da IA. Qualquer coisa fora do esperado vira None (a
    heurística segue valendo): campo desconhecido, índice fora da faixa, coluna
    repetida ou tipo errado."""
    if not text:
        return None
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    result: dict[str, int | None] = dict.fromkeys(FIELDS)
    used: set[int] = set()
    for field in FIELDS:
        value = data.get(field)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            return None
        if value < 0 or value >= n_columns or value in used:
            return None
        result[field] = value
        used.add(value)
    return result


def merge(
    heuristic: dict[str, int | None], ai: dict[str, int | None]
) -> dict[str, int | None]:
    """A heurística manda onde achou; a IA só preenche o que faltou."""
    merged = dict(heuristic)
    used = {v for v in merged.values() if v is not None}
    for field in FIELDS:
        if merged[field] is None and ai.get(field) is not None and ai[field] not in used:
            merged[field] = ai[field]
            used.add(ai[field])  # type: ignore[arg-type]
    return merged
