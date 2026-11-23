"""Alerta de procedimento no prejuízo (AI-04).

A REGRA é determinística e vive aqui, no backend. A IA só explica em texto os
números que a regra já escolheu (com checagem de números, como no AI-03); ela
nunca decide o que é prejuízo nem sugere preço.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from app.domain.ai.grounding import allowed_numbers
from app.domain.financial.procedure_ranking import ProcedureRankingRow

# Abaixo desta margem (lucro / faturado) o procedimento entra em "margem baixa".
LOW_MARGIN = Decimal("0.15")
MAX_ALERTS = 3
MAX_EXPLANATION_CHARS = 700

Kind = Literal["loss", "low_margin"]

SYSTEM_PROMPT = (
    "Você escreve, em português do Brasil, um aviso curto para uma esteticista "
    "autônoma sobre procedimentos que estão dando pouco ou nenhum lucro, em 3 a "
    "5 frases, tom direto e acolhedor. Use somente os números fornecidos, "
    "exatamente como estão; não calcule, não compare com outros períodos e não "
    "invente valor. Não sugira preço nem desconto. Sugira revisar o custo dos "
    "insumos, a taxa da forma de pagamento e o preço cobrado. Diga que os "
    "valores podem incluir custos estimados. Responda apenas com o texto."
)


@dataclass(frozen=True)
class LossAlert:
    procedure_id: object
    procedure_name: str
    kind: Kind
    gross_revenue: Decimal
    net_profit: Decimal
    margin_percent: int | None  # inteiro arredondado; None = sem faturamento
    session_count: int


def _percent(margin: Decimal | None) -> int | None:
    if margin is None:
        return None
    return int((margin * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def detect_loss_alerts(
    rows: list[ProcedureRankingRow],
    *,
    low_margin: Decimal = LOW_MARGIN,
    limit: int = MAX_ALERTS,
) -> list[LossAlert]:
    """Procedimentos com lucro negativo ou margem abaixo do limite, os piores
    primeiro. Linha sem margem calculável (faturado zero) não gera alerta: sem
    número confiável, sem aviso."""
    alerts: list[LossAlert] = []
    for r in rows:
        if r.margin is None:
            continue
        if r.net_profit < 0:
            kind: Kind = "loss"
        elif r.margin < low_margin:
            kind = "low_margin"
        else:
            continue
        alerts.append(
            LossAlert(
                procedure_id=r.procedure_id,
                procedure_name=r.procedure_name,
                kind=kind,
                gross_revenue=r.gross_revenue,
                net_profit=r.net_profit,
                margin_percent=_percent(r.margin),
                session_count=r.session_count,
            )
        )
    alerts.sort(key=lambda a: a.net_profit)
    return alerts[:limit]


def _brl(value: Decimal) -> str:
    inteiro, _, dec = f"{value:.2f}".partition(".")
    sinal = "-" if inteiro.startswith("-") else ""
    inteiro = inteiro.lstrip("-")
    grupos: list[str] = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    return f"{sinal}R$ {'.'.join(grupos)},{dec}"


def build_user_prompt(alerts: list[LossAlert]) -> str:
    linhas = []
    for a in alerts:
        situacao = "prejuízo" if a.kind == "loss" else "margem baixa"
        linhas.append(
            f"- {a.procedure_name}: {situacao}; faturado {_brl(a.gross_revenue)}, "
            f"lucro {_brl(a.net_profit)}, margem {a.margin_percent}%, "
            f"{a.session_count} atendimento(s)"
        )
    return "Procedimentos para revisar:\n" + "\n".join(linhas) + "\nEscreva o aviso."


def fallback_text(alerts: list[LossAlert]) -> str:
    nomes = ", ".join(a.procedure_name for a in alerts)
    return (
        f"Estes procedimentos estão com prejuízo ou margem baixa no período: {nomes}. "
        "Vale revisar o custo dos insumos, a taxa da forma de pagamento e o preço "
        "cobrado. Os valores podem incluir custos estimados."
    )


def allowed_for(alerts: list[LossAlert]) -> set[str]:
    values: list[object] = []
    for a in alerts:
        values += [a.gross_revenue, a.net_profit, a.margin_percent or 0, a.session_count]
    allowed = allowed_numbers(*values)
    # Os nomes dos procedimentos podem ter números ("Peeling 2"): são dados.
    for a in alerts:
        allowed |= allowed_numbers(a.procedure_name)
    return allowed
