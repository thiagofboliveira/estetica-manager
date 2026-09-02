"""Agrupamento e supressão da tela de reativação (MVP v7.1 §15,
TASK-030). PURO: recebe cortes estreitos de dados (dataclasses), nunca
SQLAlchemy — mesmo padrão de app.domain.financial.dashboard.

Um card por paciente, não por oportunidade (§15): 'return_interval_days
é por procedimento — Maria com Botox+Skinbooster+Limpeza apareceria três
vezes e receberia três disparos de WhatsApp na mesma semana'.
Supressão de 14 dias é por PACIENTE, independente de quantas
oportunidades ela tenha — aplicada aqui, não no service, para ficar
testável sem banco."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from app.domain.retention.window import Timing, classify_timing

_SUPPRESSION_DAYS = 14


@dataclass(frozen=True)
class OpportunityForGrouping:
    id: str
    patient_id: str
    patient_name: str
    patient_phone: str | None
    consent_whatsapp: bool
    opted_out_at: datetime | None
    last_contacted_at: datetime | None
    procedure_name: str
    due_date: date
    status: str
    potential_value: str


@dataclass(frozen=True)
class OpportunityLine:
    id: str
    procedure: str
    due_date: date
    timing: Timing
    status: str
    potential_value: str


@dataclass(frozen=True)
class PatientRetentionGroup:
    patient_id: str
    patient_name: str
    patient_phone: str | None
    can_contact: bool
    cannot_contact_reason: str | None
    total_potential_value: str
    opportunities: list[OpportunityLine]


def _cannot_contact_reason(opp: OpportunityForGrouping) -> str | None:
    if not opp.patient_phone:
        return "Paciente sem telefone cadastrado"
    if opp.opted_out_at is not None:
        return "Paciente optou por não receber mensagens"
    if not opp.consent_whatsapp:
        return "Paciente não deu consentimento para WhatsApp"
    return None


def group_by_patient(
    opportunities: list[OpportunityForGrouping],
    *,
    today: date,
    suppression_days: int = _SUPPRESSION_DAYS,
) -> list[PatientRetentionGroup]:
    by_patient: dict[str, list[OpportunityForGrouping]] = {}
    for opp in opportunities:
        by_patient.setdefault(opp.patient_id, []).append(opp)

    groups: list[PatientRetentionGroup] = []
    for patient_id, patient_opps in by_patient.items():
        last_contacted = next(
            (o.last_contacted_at for o in patient_opps if o.last_contacted_at),
            None,
        )
        if last_contacted is not None:
            days_since_contact = (today - last_contacted.date()).days
            if days_since_contact < suppression_days:
                continue

        sorted_opps = sorted(patient_opps, key=lambda o: o.due_date)
        lines = [
            OpportunityLine(
                id=o.id,
                procedure=o.procedure_name,
                due_date=o.due_date,
                timing=classify_timing(o.due_date, today),
                status=o.status,
                potential_value=o.potential_value,
            )
            for o in sorted_opps
        ]
        total = sum((Decimal(o.potential_value) for o in patient_opps), Decimal("0.00"))
        first = patient_opps[0]
        groups.append(
            PatientRetentionGroup(
                patient_id=patient_id,
                patient_name=first.patient_name,
                patient_phone=first.patient_phone,
                can_contact=all(_cannot_contact_reason(o) is None for o in patient_opps),
                cannot_contact_reason=_cannot_contact_reason(first),
                total_potential_value=str(total.quantize(Decimal("0.01"))),
                opportunities=lines,
            )
        )

    groups.sort(key=lambda g: Decimal(g.total_potential_value), reverse=True)
    return groups
