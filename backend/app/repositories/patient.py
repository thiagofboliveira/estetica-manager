from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.sql import Select

from app.models.booking import Booking, BookingStatus
from app.models.patient import Gender, Patient
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.session import Session as SessionModel
from app.models.session import SessionStatus
from app.repositories.base import TenantRepository


class PatientRepository(TenantRepository[Patient]):
    model = Patient

    def _filtered(
        self,
        search: str | None,
        gender: Gender | None = None,
        has_upcoming_booking: bool | None = None,
        has_completed_treatment: bool | None = None,
    ) -> Select:
        """Base de SELECT compartilhada por list() e count() — mesmo
        filtro de ativos/busca/atributos, para a contagem bater com a
        listagem."""
        stmt = self._scoped().where(Patient.is_active.is_(True))
        if search:
            needle = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    func.unaccent(Patient.name).ilike(func.unaccent(needle)),
                    Patient.phone.ilike(needle),
                )
            )
        if gender is not None:
            stmt = stmt.where(Patient.gender == gender)
        if has_upcoming_booking is not None:
            upcoming = self._upcoming_booking_subquery()
            stmt = stmt.where(Patient.id.in_(upcoming) if has_upcoming_booking else Patient.id.not_in(upcoming))
        if has_completed_treatment is not None:
            treated = self._completed_treatment_subquery()
            stmt = stmt.where(Patient.id.in_(treated) if has_completed_treatment else Patient.id.not_in(treated))
        return stmt

    def _upcoming_booking_subquery(self):
        """Paciente "tem agendamento" = Session futura agendável (via
        SaleItem/Sale — Session não tem patient_id direto, I5) OU
        Booking ainda não convertido com horário futuro (decidido —
        ambos contam)."""
        upcoming_sessions = (
            select(Sale.patient_id)
            .select_from(SessionModel)
            .join(SaleItem, SaleItem.id == SessionModel.sale_item_id)
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(SessionModel.professional_id == self._professional_id)
            .where(SessionModel.scheduled_at >= func.now())
            .where(SessionModel.status.in_([SessionStatus.SCHEDULED, SessionStatus.CONFIRMED]))
        )
        upcoming_bookings = (
            select(Booking.patient_id)
            .where(Booking.professional_id == self._professional_id)
            .where(Booking.scheduled_at >= func.now())
            .where(Booking.status == BookingStatus.SCHEDULED)
            .where(Booking.patient_id.is_not(None))
        )
        return upcoming_sessions.union(upcoming_bookings)

    def _completed_treatment_subquery(self):
        """Paciente "já tratou" = Session COMPLETED (via SaleItem/Sale)
        OU Sale (mesmo sem sessão vinculada, ex. produto revendido) —
        decidido."""
        completed_sessions = (
            select(Sale.patient_id)
            .select_from(SessionModel)
            .join(SaleItem, SaleItem.id == SessionModel.sale_item_id)
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(SessionModel.professional_id == self._professional_id)
            .where(SessionModel.status == SessionStatus.COMPLETED)
        )
        sales = select(Sale.patient_id).where(Sale.professional_id == self._professional_id)
        return completed_sessions.union(sales)

    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        search: str | None = None,
        gender: Gender | None = None,
        has_upcoming_booking: bool | None = None,
        has_completed_treatment: bool | None = None,
    ) -> list[Patient]:
        """Lista ativos, com busca opcional por nome (case/acento-insensível
        via unaccent — requer a extensão habilitada na migration)."""
        stmt = (
            self._filtered(search, gender, has_upcoming_booking, has_completed_treatment)
            .order_by(Patient.name)
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(stmt))

    def count(
        self,
        *,
        search: str | None = None,
        gender: Gender | None = None,
        has_upcoming_booking: bool | None = None,
        has_completed_treatment: bool | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(
            self._filtered(search, gender, has_upcoming_booking, has_completed_treatment).subquery()
        )
        return self._session.scalar(stmt) or 0

    def list_existing_phones(self) -> set[str]:
        """Retorna todos os números de telefone de pacientes cadastrados do tenant (TASK-BACK-S2-14)."""
        stmt = self._scoped().where(Patient.phone.is_not(None)).with_only_columns(Patient.phone)
        return {p for p in self._session.scalars(stmt) if p}

    def list_never_treated(self, *, limit: int = 20, offset: int = 0) -> list[Patient]:
        """F4-02: pacientes ativos sem nenhuma Session COMPLETED nem Sale
        (reaproveita _completed_treatment_subquery, invertida). Reengajamento
        (captação de paciente frio) — não é o motor de retorno real (I6),
        entra como seção à parte em "Quem chamar hoje"."""
        stmt = (
            self._filtered(search=None, has_completed_treatment=False)
            .order_by(Patient.name)
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(stmt))

    def count_never_treated(self) -> int:
        stmt = select(func.count()).select_from(
            self._filtered(search=None, has_completed_treatment=False).subquery()
        )
        return self._session.scalar(stmt) or 0

    def _last_completed_session_subquery(self):
        """Última Session COMPLETED de cada paciente (via SaleItem/Sale,
        Session não tem patient_id direto, I5) — base de "parado há X
        dias". Só considera pacientes que JÁ trataram ao menos uma vez;
        quem nunca tratou pertence a list_never_treated(), não aqui."""
        return (
            select(Sale.patient_id.label("patient_id"), func.max(SessionModel.completed_at).label("last_treated_at"))
            .select_from(SessionModel)
            .join(SaleItem, SaleItem.id == SessionModel.sale_item_id)
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(SessionModel.professional_id == self._professional_id)
            .where(SessionModel.status == SessionStatus.COMPLETED)
            .group_by(Sale.patient_id)
            .subquery()
        )

    def _inactive_for_days_base(self, days: int):
        """Base compartilhada por list_inactive_for_days()/count_inactive_for_days()
        — mesma subquery de join, para a contagem bater com a listagem."""
        last_treated = self._last_completed_session_subquery()
        cutoff = func.now() - func.make_interval(0, 0, 0, days)
        return (
            select(Patient, last_treated.c.last_treated_at)
            .select_from(Patient)
            .where(Patient.professional_id == self._professional_id)
            .where(Patient.is_active.is_(True))
            .join(last_treated, last_treated.c.patient_id == Patient.id)
            .where(last_treated.c.last_treated_at < cutoff)
        )

    def list_inactive_for_days(
        self, days: int, *, limit: int = 20, offset: int = 0
    ) -> list[tuple[Patient, datetime]]:
        """F4-03: pacientes ativos cuja última Session COMPLETED foi há
        mais de `days` dias, junto com essa data (para exibir "há quanto
        tempo" na UI). `days` é parâmetro de chamada, não config salva
        (pedido explícito do usuário — "variável"). Não exclui
        oportunidade de retorno já aberta aqui: essa checagem é feita
        pelo RetentionService, que já enxerga as duas fontes para não
        duplicar cartão na tela."""
        stmt = (
            self._inactive_for_days_base(days)
            .order_by("last_treated_at")
            .limit(limit)
            .offset(offset)
        )
        return [(row[0], row[1]) for row in self._session.execute(stmt)]

    def count_inactive_for_days(self, days: int) -> int:
        stmt = select(func.count()).select_from(self._inactive_for_days_base(days).subquery())
        return self._session.scalar(stmt) or 0
