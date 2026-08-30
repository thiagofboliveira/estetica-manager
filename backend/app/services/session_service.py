from datetime import UTC, date, datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo

from app.core.money import money
from app.domain.retention.enums import ReturnOpportunityStatus
from app.domain.retention.opportunity_rules import calculate_due_date
from app.domain.sales.session_state_machine import SessionStatus, validate_transition
from app.models.return_opportunity import ReturnOpportunity
from app.models.session import Session
from app.repositories.booking import BookingRepository
from app.repositories.patient import PatientRepository
from app.repositories.procedure import ProcedureRepository
from app.repositories.professional import ProfessionalRepository
from app.repositories.return_opportunity import ReturnOpportunityRepository
from app.repositories.sale import SaleRepository
from app.repositories.sale_item import SaleItemRepository
from app.repositories.session import SessionRepository
from app.schemas.session import AgendaItemOut, OpenPackageOut, SessionUpdate


class SessionNotFoundError(Exception):
    pass


class SessionService:
    def __init__(
        self,
        session_repo: SessionRepository,
        sale_item_repo: SaleItemRepository,
        sale_repo: SaleRepository,
        procedure_repo: ProcedureRepository,
        patient_repo: PatientRepository,
        booking_repo: BookingRepository,
        return_opportunity_repo: ReturnOpportunityRepository,
        professional_repo: ProfessionalRepository,
    ) -> None:
        self._sessions = session_repo
        self._sale_items = sale_item_repo
        self._sales = sale_repo
        self._procedures = procedure_repo
        self._patients = patient_repo
        self._bookings = booking_repo
        self._return_opportunities = return_opportunity_repo
        self._professionals = professional_repo

    def get(self, session_id: UUID) -> Session:
        session = self._sessions.get_by_id(session_id)
        if session is None:
            raise SessionNotFoundError()
        return session

    def update(self, session_id: UUID, dto: SessionUpdate) -> tuple[Session, list[str]]:
        session = self.get(session_id)
        warnings: list[str] = []

        if dto.scheduled_at is not None:
            # Verifica conflitos (aviso, sem bloqueio — MVP v6 §16.3, TASK-033)
            session_conflicts = self._sessions.find_conflicts(
                dto.scheduled_at, exclude_session_id=session.id
            )
            booking_conflicts = self._bookings.find_conflicts(dto.scheduled_at)
            if session_conflicts or booking_conflicts:
                warnings.append(
                    f"Aviso: Já existe atendimento agendado para o horário {dto.scheduled_at.isoformat()}."
                )

            session.scheduled_at = dto.scheduled_at
            if session.status == SessionStatus.PENDING:
                validate_transition(session.status, SessionStatus.SCHEDULED)
                session.status = SessionStatus.SCHEDULED

        if dto.status is not None and dto.status != session.status:
            validate_transition(session.status, dto.status)
            session.status = dto.status

            if dto.status == SessionStatus.COMPLETED:
                if session.completed_at is None:
                    session.completed_at = datetime.now(UTC)

                # Verifica se é a última sessão do item para gerar oportunidade de retorno (TASK-025/TASK-026)
                self._check_and_create_return_opportunity(session)

            elif dto.status == SessionStatus.EXPIRED:
                # Recalcula custo realizado da venda excluindo sessões expiradas (T-018a)
                self._recalculate_sale_cost_realized(session.sale_item_id)

        if dto.cost_override is not None:
            session.cost_override = money(dto.cost_override)
            self._recalculate_sale_cost_realized(session.sale_item_id)

        if dto.notes is not None:
            session.notes = dto.notes

        self._sessions.flush()
        return session, warnings

    def _check_and_create_return_opportunity(self, session: Session) -> None:
        sale_item = self._sale_items.get(session.sale_item_id)
        if not sale_item:
            return

        all_sessions = self._sessions.list_for_sale_item(sale_item.id)
        # Se todas as outras sessões do item foram concluídas ou expiradas, dispara oportunidade de retorno
        all_finished = all(
            s.id == session.id
            or s.status
            in (
                SessionStatus.COMPLETED,
                SessionStatus.EXPIRED,
                SessionStatus.CANCELLED,
            )
            for s in all_sessions
        )

        if all_finished:
            interval = (
                sale_item.return_interval_applied
                if sale_item.return_interval_applied is not None
                else 0
            )
            if interval > 0:
                sale = self._sales.get(sale_item.sale_id)
                if sale:
                    due = calculate_due_date(
                        (session.completed_at or datetime.now(UTC)).date(), interval
                    )
                    # Verifica se já não existe oportunidade idêntica aberta
                    existing = (
                        self._return_opportunities.find_open_for_patient_and_procedure(
                            sale.patient_id, sale_item.procedure_id
                        )
                    )
                    if not existing:
                        opp = ReturnOpportunity(
                            patient_id=sale.patient_id,
                            procedure_id=sale_item.procedure_id,
                            source_sale_item_id=sale_item.id,
                            due_date=due,
                            status=ReturnOpportunityStatus.OPEN,
                        )
                        self._return_opportunities.add(opp)

    def _recalculate_sale_cost_realized(self, sale_item_id: UUID) -> None:
        sale_item = self._sale_items.get(sale_item_id)
        if not sale_item:
            return
        sale = self._sales.get(sale_item.sale_id)
        if not sale:
            return

        items = self._sale_items.list_for_sale(sale.id)
        total_realized = money("0.00")

        for item in items:
            sessions = self._sessions.list_for_sale_item(item.id)
            if not sessions:
                continue
            cost_per_session = money(item.unit_cost_estimated / len(sessions))
            for s in sessions:
                if s.status != SessionStatus.EXPIRED:
                    if s.cost_override is not None:
                        total_realized += s.cost_override
                    else:
                        total_realized += cost_per_session

        sale.cost_realized = total_realized

    def get_agenda(self, from_date: date, to_date: date) -> list[AgendaItemOut]:
        prof = self._professionals.get_by_id(self._sessions._professional_id)
        tz_name = prof.timezone if prof and prof.timezone else "America/Sao_Paulo"
        tz = ZoneInfo(tz_name)

        start_dt = datetime.combine(from_date, time.min).replace(tzinfo=tz)
        end_dt = datetime.combine(to_date, time.max).replace(tzinfo=tz)

        scheduled_sessions = self._sessions.list_scheduled_in_range(start_dt, end_dt)
        scheduled_bookings = self._bookings.list_in_range(
            start_dt, end_dt, status=SessionStatus.SCHEDULED
        )

        agenda: list[AgendaItemOut] = []

        # Cache de items/sales/procedures/patients para evitar N+1 queries
        items_cache = {}
        sales_cache = {}
        procs_cache = {}
        patients_cache = {}

        for sess in scheduled_sessions:
            if not sess.scheduled_at:
                continue
            if sess.sale_item_id not in items_cache:
                items_cache[sess.sale_item_id] = self._sale_items.get(sess.sale_item_id)
            sale_item = items_cache[sess.sale_item_id]
            if not sale_item:
                continue

            if sale_item.sale_id not in sales_cache:
                sales_cache[sale_item.sale_id] = self._sales.get(sale_item.sale_id)
            sale = sales_cache[sale_item.sale_id]
            if not sale:
                continue

            if sale_item.procedure_id not in procs_cache:
                procs_cache[sale_item.procedure_id] = self._procedures.get(
                    sale_item.procedure_id
                )
            proc = procs_cache[sale_item.procedure_id]

            if sale.patient_id not in patients_cache:
                patients_cache[sale.patient_id] = self._patients.get(sale.patient_id)
            patient = patients_cache[sale.patient_id]

            agenda.append(
                AgendaItemOut(
                    id=sess.id,
                    type="SESSION",
                    patient_id=sale.patient_id,
                    patient_name=patient.name if patient else "Paciente",
                    patient_phone=patient.phone if patient else None,
                    procedure_name=proc.name if proc else "Procedimento",
                    scheduled_at=sess.scheduled_at,
                    modality=sess.modality,
                    status=sess.status.value,
                    sequence_number=sess.sequence_number,
                    total_sessions=sale_item.quantity,
                    note=sess.notes,
                )
            )

        for b in scheduled_bookings:
            p_name = (
                b.patient.name if b.patient else (b.patient_name_hint or "Contato novo")
            )
            p_phone = b.patient.phone if b.patient else None
            agenda.append(
                AgendaItemOut(
                    id=b.id,
                    type="BOOKING",
                    patient_id=b.patient_id,
                    patient_name=p_name,
                    patient_phone=p_phone,
                    procedure_name="Agendamento Provisório",
                    scheduled_at=b.scheduled_at,
                    modality=b.modality,
                    status=b.status.value,
                    note=b.note,
                )
            )

        agenda.sort(key=lambda item: item.scheduled_at)
        return agenda

    def get_open_packages(self) -> list[OpenPackageOut]:
        pending_sessions = self._sessions.list_open_package_sessions()
        grouped: dict[UUID, list[Session]] = {}
        for s in pending_sessions:
            grouped.setdefault(s.sale_item_id, []).append(s)

        result: list[OpenPackageOut] = []

        for sale_item_id, p_sessions in grouped.items():
            sale_item = self._sale_items.get(sale_item_id)
            if not sale_item:
                continue
            sale = self._sales.get(sale_item.sale_id)
            if not sale:
                continue
            patient = self._patients.get(sale.patient_id)
            proc = self._procedures.get(sale_item.procedure_id)

            all_sessions = self._sessions.list_for_sale_item(sale_item_id)
            completed_sessions = [
                s for s in all_sessions if s.status == SessionStatus.COMPLETED
            ]
            last_completed = (
                max(
                    (s.completed_at for s in completed_sessions if s.completed_at),
                    default=None,
                )
                if completed_sessions
                else None
            )

            p_sessions.sort(key=lambda s: s.sequence_number)
            next_session_id = p_sessions[0].id if p_sessions else None

            result.append(
                OpenPackageOut(
                    sale_id=sale.id,
                    sale_item_id=sale_item.id,
                    patient_id=sale.patient_id,
                    patient_name=patient.name if patient else "Paciente",
                    patient_phone=patient.phone if patient else None,
                    procedure_id=sale_item.procedure_id,
                    procedure_name=proc.name if proc else "Procedimento",
                    total_sessions=len(all_sessions),
                    used_sessions=len(all_sessions) - len(p_sessions),
                    pending_sessions=len(p_sessions),
                    last_session_completed_at=last_completed,
                    next_pending_session_id=next_session_id,
                )
            )

        result.sort(
            key=lambda pkg: (
                -pkg.pending_sessions,
                pkg.last_session_completed_at or datetime.min.replace(tzinfo=UTC),
            )
        )
        return result
