from datetime import UTC, date, datetime
from uuid import UUID

from app.core.money import money
from app.core.tz import today_in_timezone
from app.domain.retention.enums import ReturnOpportunityStatus
from app.domain.retention.opportunity_rules import (
    OpportunityItem,
    calculate_timing,
    group_opportunities_by_patient,
)
from app.domain.retention.state_machine import validate_return_transition
from app.models.return_opportunity import ReturnOpportunity
from app.repositories.patient import PatientRepository
from app.repositories.procedure import ProcedureRepository
from app.repositories.professional import ProfessionalRepository
from app.repositories.return_opportunity import ReturnOpportunityRepository
from app.schemas.retention import (
    OpportunityItemOut,
    PatientRetentionCardOut,
    ReturnOpportunityOut,
    ReturnOpportunityUpdate,
)


class ReturnOpportunityNotFoundError(Exception):
    pass


class RetentionService:
    def __init__(
        self,
        return_opportunity_repo: ReturnOpportunityRepository,
        patient_repo: PatientRepository,
        procedure_repo: ProcedureRepository,
        professional_repo: ProfessionalRepository,
    ) -> None:
        self._opps = return_opportunity_repo
        self._patients = patient_repo
        self._procedures = procedure_repo
        self._professionals = professional_repo

    def _get_today(self) -> date:
        prof = self._professionals.get_by_id(self._opps._professional_id)
        tz = prof.timezone if prof and prof.timezone else "America/Sao_Paulo"
        return today_in_timezone(tz)

    def get(self, opp_id: UUID) -> ReturnOpportunity:
        opp = self._opps.get_by_id(opp_id)
        if opp is None:
            raise ReturnOpportunityNotFoundError()
        return opp

    def list_cards(
        self, reference_date: date | None = None
    ) -> list[PatientRetentionCardOut]:
        today = reference_date or self._get_today()
        opps = self._opps.list_active()

        patient_cache = {}
        proc_cache = {}
        tuples_for_grouping = []

        for opp in opps:
            if opp.patient_id not in patient_cache:
                patient_cache[opp.patient_id] = self._patients.get(opp.patient_id)
            patient = patient_cache[opp.patient_id]
            if not patient or not patient.is_active:
                continue

            if opp.procedure_id not in proc_cache:
                proc_cache[opp.procedure_id] = self._procedures.get(opp.procedure_id)
            proc = proc_cache[opp.procedure_id]
            proc_name = proc.name if proc else "Procedimento"
            pot_val = proc.price if proc else money("0.00")

            timing = calculate_timing(opp.due_date, today)
            days_diff = (opp.due_date - today).days

            opp_item = OpportunityItem(
                id=opp.id,
                procedure_id=opp.procedure_id,
                procedure_name=proc_name,
                due_date=opp.due_date,
                timing=timing,
                status=opp.status,
                potential_value=pot_val,
                days_diff=days_diff,
            )

            tuples_for_grouping.append(
                (
                    patient.id,
                    patient.name,
                    patient.phone,
                    patient.consent_whatsapp,
                    patient.opted_out_at is not None,
                    opp.contacted_at,
                    opp_item,
                )
            )

        groups = group_opportunities_by_patient(tuples_for_grouping, today)

        result: list[PatientRetentionCardOut] = []
        for g in groups:
            result.append(
                PatientRetentionCardOut(
                    patient_id=g.patient_id,
                    patient_name=g.patient_name,
                    patient_phone=g.patient_phone,
                    consent_whatsapp=g.consent_whatsapp,
                    opted_out=g.opted_out,
                    is_suppressed=g.is_suppressed,
                    last_contacted_at=g.last_contacted_at,
                    total_potential_value=g.total_potential_value,
                    primary_opportunity=OpportunityItemOut(
                        id=g.primary_opportunity.id,
                        procedure_id=g.primary_opportunity.procedure_id,
                        procedure_name=g.primary_opportunity.procedure_name,
                        due_date=g.primary_opportunity.due_date,
                        timing=g.primary_opportunity.timing,
                        status=g.primary_opportunity.status,
                        potential_value=g.primary_opportunity.potential_value,
                        days_diff=g.primary_opportunity.days_diff,
                    ),
                    secondary_opportunities=[
                        OpportunityItemOut(
                            id=sec.id,
                            procedure_id=sec.procedure_id,
                            procedure_name=sec.procedure_name,
                            due_date=sec.due_date,
                            timing=sec.timing,
                            status=sec.status,
                            potential_value=sec.potential_value,
                            days_diff=sec.days_diff,
                        )
                        for sec in g.secondary_opportunities
                    ],
                    whatsapp_enabled=g.whatsapp_enabled,
                    disabled_reason=g.disabled_reason,
                )
            )

        return result

    def list_all(
        self, statuses: list[ReturnOpportunityStatus] | None = None
    ) -> list[ReturnOpportunityOut]:
        today = self._get_today()
        opps = self._opps.list_active(statuses)
        result = []

        patient_cache = {}
        proc_cache = {}

        for opp in opps:
            if opp.patient_id not in patient_cache:
                patient_cache[opp.patient_id] = self._patients.get(opp.patient_id)
            patient = patient_cache[opp.patient_id]

            if opp.procedure_id not in proc_cache:
                proc_cache[opp.procedure_id] = self._procedures.get(opp.procedure_id)
            proc = proc_cache[opp.procedure_id]

            timing = calculate_timing(opp.due_date, today)
            pot_val = proc.price if proc else money("0.00")

            result.append(
                ReturnOpportunityOut(
                    id=opp.id,
                    patient_id=opp.patient_id,
                    patient_name=patient.name if patient else "Paciente",
                    patient_phone=patient.phone if patient else None,
                    procedure_id=opp.procedure_id,
                    procedure_name=proc.name if proc else "Procedimento",
                    source_sale_item_id=opp.source_sale_item_id,
                    due_date=opp.due_date,
                    timing=timing,
                    status=opp.status,
                    potential_value=pot_val,
                    contacted_at=opp.contacted_at,
                    contact_channel=opp.contact_channel,
                    contact_status=opp.contact_status,
                    resolved_by_sale_id=opp.resolved_by_sale_id,
                    dismissed_at=opp.dismissed_at,
                    created_at=opp.created_at,
                    updated_at=opp.updated_at,
                )
            )
        return result

    def update(self, opp_id: UUID, dto: ReturnOpportunityUpdate) -> ReturnOpportunity:
        opp = self.get(opp_id)

        if dto.dismissed:
            validate_return_transition(opp.status, ReturnOpportunityStatus.DISMISSED)
            opp.status = ReturnOpportunityStatus.DISMISSED
            opp.dismissed_at = datetime.now(UTC)
        elif dto.status is not None:
            validate_return_transition(opp.status, dto.status)
            opp.status = dto.status

        if dto.contacted_at is not None:
            opp.contacted_at = dto.contacted_at
        elif (
            dto.status == ReturnOpportunityStatus.CONTACTED and opp.contacted_at is None
        ):
            opp.contacted_at = datetime.now(UTC)

        if dto.contact_channel is not None:
            opp.contact_channel = dto.contact_channel
        if dto.contact_status is not None:
            opp.contact_status = dto.contact_status

        self._opps.flush()
        return opp
