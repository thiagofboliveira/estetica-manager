"""SaleService — orquestra POST /sales (MVP v6 §11 TASK-015, §12 motor de
lucro).

Camada de orquestração (backend/ENGENHARIA.md §5): busca config +
procedimentos, monta LineItem puro, chama o domínio
(app.domain.financial.calculator), persiste o snapshot congelado e gera
as N sessões. O CÁLCULO em si vive em domain/ — testável sem banco.

Idempotência (T-015a, contrato C-1): mesma Idempotency-Key + mesmo corpo
em 24h -> devolve a MESMA venda (200), nunca cria duplicata. Chave igual
com corpo DIFERENTE é erro 409 (o corpo mudou, a intenção não é a
mesma) — chave diferente com mesmo corpo é uma NOVA venda de propósito
(duplo clique acidental usa a mesma chave; duas vendas legítimas
iguais no mesmo dia usam chaves diferentes, geradas pelo cliente).
"""

import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID

from app.core.money import money
from app.core.tz import today_in_timezone
from app.domain.bookings.enums import BookingStatus
from app.domain.financial.calculator import (
    FeePayer as CalcFeePayer,
)
from app.domain.financial.calculator import (
    FeeRule as CalcFeeRule,
)
from app.domain.financial.calculator import (
    LineItem as CalcLineItem,
)
from app.domain.financial.calculator import (
    PaymentMethod as CalcPaymentMethod,
)
from app.domain.financial.calculator import (
    SaleCalculationResult,
    SaleParams,
    calculate_sale,
    expected_receipt_date,
)
from app.domain.financial.calculator import (
    SplitBase as CalcSplitBase,
)
from app.models.sale import Sale, SaleStatus
from app.models.sale_item import SaleItem
from app.models.session import Session as SessionModel
from app.models.session import SessionStatus
from app.repositories.booking import BookingRepository
from app.repositories.financial_settings import FinancialSettingsRepository
from app.repositories.patient import PatientRepository
from app.repositories.payment_fee_rule import PaymentFeeRuleRepository
from app.repositories.procedure import ProcedureRepository
from app.repositories.professional import ProfessionalRepository
from app.repositories.return_opportunity import ReturnOpportunityRepository
from app.repositories.sale import SaleRepository
from app.repositories.sale_item import SaleItemRepository
from app.repositories.session import SessionRepository
from app.schemas.sale import SaleCreate
from app.services.financial_settings_service import FinancialSettingsService

IDEMPOTENCY_TTL_HOURS = 24


class PatientNotFoundForSaleError(Exception):
    pass


class ProcedureNotFoundForSaleError(Exception):
    def __init__(self, procedure_id: UUID) -> None:
        self.procedure_id = procedure_id
        super().__init__(f"procedimento não encontrado: {procedure_id}")


class SaleNotFoundError(Exception):
    pass


class IdempotencyKeyConflictError(Exception):
    """Mesma chave, corpo diferente — a intenção mudou, não é o mesmo
    clique duplicado. 409, nunca silenciosamente ignorado."""


def _hash_body(dto: SaleCreate) -> str:
    payload = dto.model_dump(mode="json")
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class SaleService:
    def __init__(
        self,
        sale_repo: SaleRepository,
        sale_item_repo: SaleItemRepository,
        session_repo: SessionRepository,
        procedure_repo: ProcedureRepository,
        patient_repo: PatientRepository,
        financial_settings_repo: FinancialSettingsRepository,
        payment_fee_rule_repo: PaymentFeeRuleRepository,
        professional_repo: ProfessionalRepository,
        booking_repo: BookingRepository | None = None,
        return_opportunity_repo: ReturnOpportunityRepository | None = None,
    ) -> None:
        self._sales = sale_repo
        self._sale_items = sale_item_repo
        self._sessions = session_repo
        self._procedures = procedure_repo
        self._patients = patient_repo
        self._financial_settings = financial_settings_repo
        self._payment_fee_rules = payment_fee_rule_repo
        self._professionals = professional_repo
        self._bookings = booking_repo
        self._return_opportunities = return_opportunity_repo

    def find_existing_by_idempotency_key(self, idempotency_key: str) -> Sale | None:
        """Usado pela rota só para decidir 200 vs 201 na resposta — a
        decisão de negócio (reusar vs conflitar) continua em create()."""
        return self._sales.find_by_idempotency_key(idempotency_key)

    def create(self, dto: SaleCreate, idempotency_key: str | None) -> Sale:
        body_hash = _hash_body(dto)

        if idempotency_key:
            existing = self._sales.find_by_idempotency_key(idempotency_key)
            if existing is not None:
                if existing.idempotency_body_hash != body_hash:
                    raise IdempotencyKeyConflictError()
                age = datetime.now(UTC) - existing.created_at
                if age.total_seconds() <= IDEMPOTENCY_TTL_HOURS * 3600:
                    return existing
                # TTL expirado: cai para o fluxo normal e cria uma venda
                # nova com a mesma chave (sobrescreve o registro antigo
                # de controle, não afeta a venda expirada já criada).

        if self._patients.get(dto.patient_id) is None:
            raise PatientNotFoundForSaleError()

        procedures = {
            item.procedure_id: self._procedures.get(item.procedure_id)
            for item in dto.items
        }
        for pid, proc in procedures.items():
            if proc is None:
                raise ProcedureNotFoundForSaleError(pid)

        settings = self._financial_settings_or_default()
        fee_rules = self._payment_fee_rules.list_for_method(dto.payment_method.value)
        line_items = [
            CalcLineItem(
                unit_price=proc.price,
                quantity=item.quantity,
                unit_cost_estimated=proc.estimated_cost,
                session_costs=[proc.estimated_cost] * item.quantity,
                split_override=proc.split_override,
            )
            for item, proc in ((i, procedures[i.procedure_id]) for i in dto.items)
        ]

        # Converte enum do modelo para o enum puro do domínio (backend/ENGENHARIA.md §5:
        # domain/ não importa models nem schemas).
        params = SaleParams(
            discount_amount=money(dto.discount_amount),
            payment_method=CalcPaymentMethod(dto.payment_method.value),
            installments=dto.installments,
            split_clinic_percentage=settings.split_clinic_percentage,
            split_base=CalcSplitBase(settings.split_base.value),
            fee_payer=CalcFeePayer(settings.fee_payer.value),
            fee_rules=[
                CalcFeeRule(
                    installments_min=r.installments_min,
                    installments_max=r.installments_max,
                    fee_percentage=r.fee_percentage,
                )
                for r in fee_rules
            ],
            anticipates_all=settings.anticipates_all,
            anticipation_rate_per_installment=settings.anticipation_rate_per_installment,
        )

        result: SaleCalculationResult = calculate_sale(line_items, params)

        prof = self._professionals.get_by_id(self._sales._professional_id)
        tz_name = prof.timezone if prof and prof.timezone else "America/Sao_Paulo"
        today = today_in_timezone(tz_name)

        expected_receipt = expected_receipt_date(
            CalcPaymentMethod(dto.payment_method.value),
            today,
            dto.installments,
            anticipates=settings.anticipates_all,
        )

        sale = Sale(
            patient_id=dto.patient_id,
            type=dto.type,
            sold_at=today,
            status=SaleStatus.ACTIVE,
            payment_method=dto.payment_method,
            installments=dto.installments,
            items_total=result.items_total,
            discount_amount=result.discount_amount,
            gross_amount=result.gross_amount,
            split_applied=result.split_rate,
            split_base_applied=settings.split_base,
            split_amount_applied=result.split_amount,
            fee_payer_applied=settings.fee_payer,
            fee_applied=result.fee_rate,
            fee_amount_applied=result.fee_amount,
            fee_amount_charged_applied=result.fee_amount_charged_to_professional,
            cost_provisioned=result.cost_provisioned,
            cost_realized=result.cost_realized,
            net_profit=result.net_profit,
            margin=result.margin,
            expected_receipt_date=expected_receipt,
            notes=dto.notes,
            snapshot_payload=_snapshot_payload(result, settings),
            idempotency_key=idempotency_key,
            idempotency_body_hash=body_hash if idempotency_key else None,
        )
        sale = self._sales.add(sale)

        # Se a venda veio de um booking, converte na mesma transação (TASK-034b, v7.1 §16.6)
        if dto.booking_id and self._bookings:
            booking = self._bookings.get_by_id(dto.booking_id)
            if booking:
                booking.status = BookingStatus.CONVERTED
                booking.sale_id = sale.id

        for item_dto, item_result in zip(dto.items, result.items, strict=True):
            proc = procedures[item_dto.procedure_id]
            sale_item = SaleItem(
                sale_id=sale.id,
                procedure_id=proc.id,
                quantity=item_dto.quantity,
                unit_price=proc.price,
                unit_cost_estimated=proc.estimated_cost,
                return_interval_applied=proc.return_interval_days,
                discount_allocated=item_result.discount_allocated,
            )
            sale_item = self._sale_items.add(sale_item)

            # Gera N sessões: PENDING se pacote (saldo, sem data),
            # SCHEDULED se avulso (§11.3/TASK-015). modality copiada de
            # procedure.default_modality NA CRIAÇÃO (v7.1) — nunca
            # resolvida por COALESCE na leitura.
            initial_status = (
                SessionStatus.PENDING
                if dto.type.value == "PACKAGE"
                else SessionStatus.SCHEDULED
            )
            for seq in range(1, item_dto.quantity + 1):
                session = SessionModel(
                    sale_item_id=sale_item.id,
                    sequence_number=seq,
                    status=initial_status,
                    modality=proc.default_modality,
                )
                self._sessions.add(session)

        # Fecha oportunidades de retorno abertas para os procedimentos comprados (TASK-028)
        if self._return_opportunities:
            procedure_ids = [it.procedure_id for it in dto.items]
            self._return_opportunities.close_for_patient_and_procedures(
                dto.patient_id, procedure_ids, sale.id
            )

        self._sales.flush()
        return sale

    def get(self, sale_id: UUID) -> Sale:
        sale = self._sales.get(sale_id)
        if sale is None:
            raise SaleNotFoundError()
        return sale

    def cancel(self, sale_id: UUID, reason: str | None = None) -> Sale:
        """Cancela venda ativa e cancela sessões não concluídas (TASK-017)."""
        sale = self.get(sale_id)
        if sale.status != SaleStatus.ACTIVE:
            raise ValueError(f"Venda com status {sale.status} não pode ser cancelada.")
        sale.status = SaleStatus.CANCELLED
        if reason:
            sale.notes = f"{sale.notes or ''} [Cancelada: {reason}]".strip()
        for item in self.get_items(sale_id):
            sessions = self._sessions.list_for_sale_item(item.id)
            for s in sessions:
                if s.status in (
                    SessionStatus.PENDING,
                    SessionStatus.SCHEDULED,
                    SessionStatus.CONFIRMED,
                ):
                    s.status = SessionStatus.CANCELLED
        self._sales.flush()
        return sale

    def refund(self, sale_id: UUID, reason: str | None = None) -> Sale:
        """Estorna venda ativa e cancela sessões pendentes/agendadas (TASK-017)."""
        sale = self.get(sale_id)
        if sale.status != SaleStatus.ACTIVE:
            raise ValueError(f"Venda com status {sale.status} não pode ser estornada.")
        sale.status = SaleStatus.REFUNDED
        if reason:
            sale.notes = f"{sale.notes or ''} [Estornada: {reason}]".strip()
        for item in self.get_items(sale_id):
            sessions = self._sessions.list_for_sale_item(item.id)
            for s in sessions:
                if s.status in (
                    SessionStatus.PENDING,
                    SessionStatus.SCHEDULED,
                    SessionStatus.CONFIRMED,
                ):
                    s.status = SessionStatus.CANCELLED
        self._sales.flush()
        return sale

    def get_items(self, sale_id: UUID) -> list[SaleItem]:
        return self._sale_items.list_for_sale(sale_id)

    def get_sessions_for_items(self, item_ids: list[UUID]) -> list[SessionModel]:
        sessions: list[SessionModel] = []
        for item_id in item_ids:
            sessions.extend(self._sessions.list_for_sale_item(item_id))
        return sessions

    def _financial_settings_or_default(self):
        return FinancialSettingsService(
            self._financial_settings
        ).get_or_create_default()


def _snapshot_payload(result: SaleCalculationResult, settings) -> dict:
    """Auditoria — payload bruto do cálculo, para reconstituir 'por que
    esse número' sem depender da config atual (invariante I3)."""
    return {
        "split_clinic_percentage": str(settings.split_clinic_percentage),
        "split_base": settings.split_base.value,
        "fee_payer": settings.fee_payer.value,
        "fee_rate": str(result.fee_rate),
        "fee_amount": str(result.fee_amount),
        "fee_amount_charged_to_professional": str(
            result.fee_amount_charged_to_professional
        ),
        "cost_provisioned": str(result.cost_provisioned),
        "cost_realized": str(result.cost_realized),
    }
