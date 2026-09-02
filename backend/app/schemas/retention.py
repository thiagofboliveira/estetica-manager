from datetime import date, datetime
from uuid import UUID

from pydantic import model_validator

from app.models.return_opportunity import ContactChannel, ReturnOpportunityStatus
from app.schemas.base import InputSchema, OutputSchema
from app.schemas.types import MoneyOut


class OpportunityLineOut(OutputSchema):
    id: UUID
    procedure: str
    due_date: date
    timing: str
    status: ReturnOpportunityStatus
    potential_value: MoneyOut


class PatientRetentionOut(OutputSchema):
    patient_id: UUID
    patient_name: str
    patient_phone: str | None
    can_contact: bool
    cannot_contact_reason: str | None
    total_potential_value: MoneyOut
    opportunities: list[OpportunityLineOut]


class ReturnOpportunityUpdate(InputSchema):
    status: ReturnOpportunityStatus
    contact_channel: ContactChannel | None = None

    @model_validator(mode="after")
    def _contact_channel_obrigatorio_para_contacted(self) -> "ReturnOpportunityUpdate":
        """Spec (design doc, ~linha 158): 'contact_channel obrigatório
        apenas quando status in (CONTACTED, ...)'. Sem isso, um PATCH para
        CONTACTED sem canal carimbava contacted_at (disparando a supressão
        de 14 dias) sem nenhum registro de como a paciente foi contatada."""
        if (
            self.status == ReturnOpportunityStatus.CONTACTED
            and self.contact_channel is None
        ):
            raise ValueError(
                "contact_channel é obrigatório ao transicionar para CONTACTED"
            )
        return self


class ReturnOpportunityOut(OutputSchema):
    id: UUID
    patient_id: UUID
    procedure_id: UUID
    due_date: date
    potential_value: MoneyOut
    status: ReturnOpportunityStatus
    contacted_at: datetime | None
    contact_channel: ContactChannel | None
    resolved_by_sale_id: UUID | None
    dismissed_at: datetime | None
