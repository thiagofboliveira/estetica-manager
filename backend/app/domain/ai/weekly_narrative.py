"""Resumo semanal narrado (AI-03).

A IA só reescreve em poucas frases números que o backend já calculou. Todo
número do texto gerado é conferido contra o payload (grounding): se aparecer
valor que não veio dos dados, o texto é descartado e vale o texto fixo.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.domain.ai.grounding import allowed_numbers

MAX_NARRATIVE_CHARS = 700

SYSTEM_PROMPT = (
    "Você escreve, em português do Brasil, um resumo curto da semana para uma "
    "esteticista autônoma, em 3 a 5 frases, tom direto e acolhedor. Use somente "
    "os números fornecidos, exatamente como estão; não calcule, não some, não "
    "compare com outras semanas, não projete e não invente nenhum valor. Chame "
    "o resultado de 'lucro', sem adjetivos como 'real' ou 'garantido'. Se houver "
    "pacientes para chamar, sugira chamá-las. Responda apenas com o texto."
)


@dataclass(frozen=True)
class WeeklyNarrativeContext:
    period_start: date
    period_end: date
    gross_revenue: Decimal
    net_profit: Decimal
    sales_count: int
    pending_opportunities_count: int


def _brl(value: Decimal) -> str:
    inteiro, _, dec = f"{value:.2f}".partition(".")
    sinal = "-" if inteiro.startswith("-") else ""
    inteiro = inteiro.lstrip("-")
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    return f"{sinal}R$ {'.'.join(grupos)},{dec}"


def _dm(d: date) -> str:
    return d.strftime("%d/%m")


def build_user_prompt(ctx: WeeklyNarrativeContext) -> str:
    return (
        f"Período: {_dm(ctx.period_start)} a {_dm(ctx.period_end)}\n"
        f"Faturado: {_brl(ctx.gross_revenue)}\n"
        f"Lucro: {_brl(ctx.net_profit)}\n"
        f"Atendimentos: {ctx.sales_count}\n"
        f"Pacientes para chamar: {ctx.pending_opportunities_count}\n"
        "Escreva o resumo."
    )


def fallback_text(ctx: WeeklyNarrativeContext) -> str:
    base = (
        f"Na semana de {_dm(ctx.period_start)} a {_dm(ctx.period_end)} você "
        f"faturou {_brl(ctx.gross_revenue)}, com lucro de {_brl(ctx.net_profit)}, "
        f"em {ctx.sales_count} atendimento(s)."
    )
    if ctx.pending_opportunities_count > 0:
        base += f" Há {ctx.pending_opportunities_count} paciente(s) para chamar."
    return base


def allowed_for(ctx: WeeklyNarrativeContext) -> set[str]:
    return allowed_numbers(
        ctx.gross_revenue,
        ctx.net_profit,
        ctx.sales_count,
        ctx.pending_opportunities_count,
        ctx.period_start.day,
        ctx.period_start.month,
        ctx.period_end.day,
        ctx.period_end.month,
    )
