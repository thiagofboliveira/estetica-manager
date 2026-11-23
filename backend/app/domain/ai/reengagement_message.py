"""Mensagem de reengajamento (AI-06): paciente que parou de voltar ou nunca tratou.

Só o primeiro nome e a situação. Sem procedimento, valor, telefone nem dado
clínico (REV-20).
"""

from dataclasses import dataclass
from typing import Literal

Kind = Literal["never_treated", "inactive"]


@dataclass(frozen=True)
class ReengagementContext:
    patient_first_name: str
    kind: Kind


def fallback_message(ctx: ReengagementContext) -> str:
    nome = ctx.patient_first_name
    saudacao = f"Oi, {nome}!" if nome else "Oi!"
    if ctx.kind == "never_treated":
        return (
            f"{saudacao} Tudo bem? Estou com horários abertos e adoraria te "
            "receber para a gente conversar sobre o que você precisa. "
            "Quer que eu veja um horário?"
        )
    return (
        f"{saudacao} Tudo bem? Faz um tempinho que a gente não se vê e lembrei "
        "de você. Quer que eu veja um horário para te receber?"
    )


def build_user_prompt(ctx: ReengagementContext) -> str:
    if ctx.kind == "never_treated":
        situacao = "ainda não fez nenhum tratamento; convide para conhecer o atendimento"
    else:
        situacao = "não volta há algum tempo; convide para retomar o cuidado"
    return (
        f"Paciente: {ctx.patient_first_name}\n"
        f"Situação: {situacao}.\n"
        "Não cite procedimento, preço, desconto nem prazo. Escreva a mensagem."
    )
