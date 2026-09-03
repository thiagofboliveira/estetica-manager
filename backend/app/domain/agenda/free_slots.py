"""Épico A — "Modo Ocupado" (MVP pós-validação, roadmap 2026-09-02).

PURO: sem SQLAlchemy, sem FastAPI, sem I/O. Calcula os horários livres
de um dia a partir da janela de trabalho configurada e dos compromissos
já ocupados (sessions + bookings, que o caller já buscou combinados via
SessionService.get_agenda).

Nenhuma entidade do domínio guarda duração hoje (Session/Booking só têm
horário de início) — por decisão de escopo, todo compromisso ocupa
exatamente `slot_minutes`, a mesma duração usada para os slots livres.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta


@dataclass(frozen=True)
class WorkWindow:
    start: time
    end: time
    slot_minutes: int
    buffer_minutes: int


@dataclass(frozen=True)
class Occupied:
    start: time


def compute_free_slots(*, occupied: list[Occupied], window: WorkWindow) -> list[time]:
    anchor = date(2000, 1, 1)
    slot_delta = timedelta(minutes=window.slot_minutes)
    buffer_delta = timedelta(minutes=window.buffer_minutes)

    cursor = datetime.combine(anchor, window.start)
    end_dt = datetime.combine(anchor, window.end)

    blocked_ranges = [
        (
            datetime.combine(anchor, o.start) - buffer_delta,
            datetime.combine(anchor, o.start) + slot_delta + buffer_delta,
        )
        for o in occupied
    ]

    slots: list[time] = []
    while cursor + slot_delta <= end_dt:
        slot_end = cursor + slot_delta
        overlaps = any(
            cursor < blocked_end and slot_end > blocked_start
            for blocked_start, blocked_end in blocked_ranges
        )
        if not overlaps:
            slots.append(cursor.time())
        cursor += slot_delta

    return slots
