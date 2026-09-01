from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from app.domain.retention.enums import ReturnOpportunityStatus, Timing


def calculate_due_date(completed_date: date, interval_days: int) -> date:
    """Calcula a data prevista de retorno (TASK-026)."""
    return completed_date + timedelta(days=interval_days)


def calculate_timing(due_date: date, reference_date: date) -> Timing:
    """
    Eixo 1 — timing derivado em runtime (MVP v6 §14, TASK-025):
    - UPCOMING: due_date > hoje + 7
    - DUE: hoje - 7 <= due_date <= hoje + 7
    - OVERDUE: due_date < hoje - 7
    """
    if due_date > reference_date + timedelta(days=7):
        return Timing.UPCOMING
    if due_date < reference_date - timedelta(days=7):
        return Timing.OVERDUE
    return Timing.DUE


def is_suppressed(
    last_contacted_at: datetime | None,
    reference_date: date,
    suppression_days: int = 14,
) -> bool:
    """
    Regra de supressão (TASK-030): paciente contatada nos últimos 14 dias
    não reaparece na lista diária de disparos.
    """
    if last_contacted_at is None:
        return False
    contact_date = last_contacted_at.date()
    return (reference_date - contact_date) < timedelta(days=suppression_days)


def is_attributed_conversion(
    contacted_at: datetime | date | None,
    sold_at: date,
    window_days: int = 21,
) -> bool:
    """
    Atribuição de receita do motor de retorno (TASK-045b, MVP v6 §15, §19):
    Uma venda só é atribuída à campanha de retorno se sold_at ocorrer
    entre contacted_at e contacted_at + 21 dias.
    """
    if contacted_at is None:
        return False
    contact_date = (
        contacted_at.date() if isinstance(contacted_at, datetime) else contacted_at
    )
    if sold_at < contact_date:
        return False
    return (sold_at - contact_date) <= timedelta(days=window_days)


@dataclass(frozen=True)
class OpportunityItem:
    id: UUID
    procedure_id: UUID
    procedure_name: str
    due_date: date
    timing: Timing
    status: ReturnOpportunityStatus
    potential_value: Decimal
    days_diff: int  # negativo = atrasado, 0 = hoje, positivo = futuro


@dataclass(frozen=True)
class PatientRetentionGroup:
    patient_id: UUID
    patient_name: str
    patient_phone: str | None
    consent_whatsapp: bool
    opted_out: bool
    is_suppressed: bool
    last_contacted_at: datetime | None
    total_potential_value: Decimal
    primary_opportunity: OpportunityItem
    secondary_opportunities: list[OpportunityItem]
    whatsapp_enabled: bool
    disabled_reason: str | None


def group_opportunities_by_patient(
    opportunities: list[
        tuple[UUID, str, str | None, bool, bool, datetime | None, OpportunityItem]
    ],
    reference_date: date,
    suppression_days: int = 14,
) -> list[PatientRetentionGroup]:
    """
    Agrupa oportunidades por paciente para o card 'Quem devo chamar hoje?' (TASK-030).
    Cada item na tupla de entrada representa:
    (patient_id, patient_name, patient_phone, consent_whatsapp, opted_out, last_contacted_at, opp_item)
    """
    by_patient: dict[UUID, dict] = {}

    for (
        patient_id,
        patient_name,
        patient_phone,
        consent_whatsapp,
        opted_out,
        last_contacted_at,
        opp,
    ) in opportunities:
        if patient_id not in by_patient:
            by_patient[patient_id] = {
                "patient_id": patient_id,
                "patient_name": patient_name,
                "patient_phone": patient_phone,
                "consent_whatsapp": consent_whatsapp,
                "opted_out": opted_out,
                "last_contacted_at": last_contacted_at,
                "items": [],
            }
        by_patient[patient_id]["items"].append(opp)

    result: list[PatientRetentionGroup] = []

    for p in by_patient.values():
        items: list[OpportunityItem] = p["items"]
        # Ordena itens do paciente: primeiro os mais atrasados (menor days_diff), depois maior valor
        items_sorted = sorted(items, key=lambda it: (it.days_diff, -it.potential_value))
        primary = items_sorted[0]
        secondary = items_sorted[1:]
        total_val = sum(it.potential_value for it in items)

        suppressed = is_suppressed(
            p["last_contacted_at"], reference_date, suppression_days
        )

        whatsapp_enabled = True
        disabled_reason = None

        if p["opted_out"]:
            whatsapp_enabled = False
            disabled_reason = "Paciente solicitou opt-out de mensagens."
        elif not p["consent_whatsapp"]:
            whatsapp_enabled = False
            disabled_reason = "Sem consentimento de WhatsApp registrado."
        elif not p["patient_phone"]:
            whatsapp_enabled = False
            disabled_reason = "Sem telefone cadastrado."
        elif suppressed:
            whatsapp_enabled = False
            disabled_reason = f"Paciente contatada recentemente (supressão de {suppression_days} dias)."

        result.append(
            PatientRetentionGroup(
                patient_id=p["patient_id"],
                patient_name=p["patient_name"],
                patient_phone=p["patient_phone"],
                consent_whatsapp=p["consent_whatsapp"],
                opted_out=p["opted_out"],
                is_suppressed=suppressed,
                last_contacted_at=p["last_contacted_at"],
                total_potential_value=total_val,
                primary_opportunity=primary,
                secondary_opportunities=secondary,
                whatsapp_enabled=whatsapp_enabled,
                disabled_reason=disabled_reason,
            )
        )

    # Ordena os cards: maior valor potencial primeiro, depois mais atrasados
    result.sort(
        key=lambda g: (-g.total_potential_value, g.primary_opportunity.days_diff)
    )
    return result
