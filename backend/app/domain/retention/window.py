"""Cálculo da janela de retorno (MVP v7.1 §11.6, §14, TASK-026).

PURO: sem SQLAlchemy, sem FastAPI (mesma disciplina de
app.domain.financial.calculator).

due_date = última sessão COMPLETED do item + return_interval_applied
(§11.6) — decisão consciente de contar a partir da ÚLTIMA sessão
realizada, não da primeira nem da data da venda.

timing é derivado de due_date vs hoje EM TODA LEITURA, nunca persistido
— muda sozinho com o tempo, ao contrário de status (evento). Janela de
±7 dias em torno de due_date é "DUE"; fora dela é UPCOMING (futuro) ou
OVERDUE (passado)."""

from datetime import date, timedelta
from enum import StrEnum

_DUE_WINDOW_DAYS = 7


class Timing(StrEnum):
    UPCOMING = "UPCOMING"
    DUE = "DUE"
    OVERDUE = "OVERDUE"


def calculate_due_date(completed_at: date, return_interval_days: int) -> date:
    return completed_at + timedelta(days=return_interval_days)


def classify_timing(due_date: date, today: date) -> Timing:
    delta_days = (due_date - today).days
    if delta_days > _DUE_WINDOW_DAYS:
        return Timing.UPCOMING
    if delta_days < -_DUE_WINDOW_DAYS:
        return Timing.OVERDUE
    return Timing.DUE
