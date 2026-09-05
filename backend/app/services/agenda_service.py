"""AgendaService — Épico A, "Modo Ocupado" (roadmap 2026-09-02).

Camada de orquestração fina: pega a agenda do dia já combinada
(sessions + bookings) de SessionService.get_agenda, converte para o
formato PURO de domain/agenda/free_slots.py, e monta a mensagem pronta
pro WhatsApp com app.domain.messaging.templates.
"""

from datetime import date
from zoneinfo import ZoneInfo

from app.domain.agenda.free_slots import Occupied, WorkWindow, compute_free_slots
from app.domain.messaging.templates import build_free_slots_message
from app.repositories.professional import ProfessionalRepository
from app.services.financial_settings_service import FinancialSettingsService
from app.services.session_service import SessionService


class AgendaService:
    def __init__(
        self,
        session_service: SessionService,
        financial_settings_service: FinancialSettingsService,
        professional_repo: ProfessionalRepository,
    ) -> None:
        self._sessions = session_service
        self._financial_settings = financial_settings_service
        self._professionals = professional_repo

    def get_free_slots(self, day: date) -> tuple[list, str]:
        settings = self._financial_settings.get_or_create_default()
        window = WorkWindow(
            start=settings.work_start_time,
            end=settings.work_end_time,
            slot_minutes=settings.slot_duration_minutes,
            buffer_minutes=settings.buffer_minutes,
        )

        professional = self._professionals.get_current()
        tz = ZoneInfo(professional.timezone)

        agenda_items = self._sessions.get_agenda(day, day)
        occupied = [
            Occupied(start=item.scheduled_at.astimezone(tz).time())
            for item in agenda_items
        ]

        slots = compute_free_slots(occupied=occupied, window=window)
        message = build_free_slots_message(slots) if slots else ""
        return slots, message
