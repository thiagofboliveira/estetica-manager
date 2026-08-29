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
from app.repositories.financial_settings import FinancialSettingsRepository
from app.repositories.patient import PatientRepository
from app.repositories.payment_fee_rule import PaymentFeeRuleRepository
from app.repositories.procedure import ProcedureRepository
from app.repositories.professional import ProfessionalRepository
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
    ) -> None:
        self._sales = sale_repo
        self._sale_items = sale_item_repo
        self._sessions = session_repo
        self._procedures = procedure_repo
        self._patients = patient_repo
        self._financial_settings = financial_settings_repo
        self._payment_fee_rules = payment_fee_rule_repo
        self._professionals = professional_repo

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

        procedures = {}
        for item in dto.items:
            proc = self._procedures.get(item.procedure_id)
            if proc is None:
                raise ProcedureNotFoundForSaleError(item.procedure_id)
            procedures[item.procedure_id] = proc

        settings = self._financial_settings_or_default()
        fee_rules = [
            CalcFeeRule(
                installments_min=r.installments_min,
                installments_max=r.installments_max,
                fee_percentage=r.fee_percentage,
                fixed_fee=r.fixed_fee,
            )
            for r in self._payment_fee_rules.list_all()
            if r.payment_method == dto.payment_method
        ]

        calc_items = [
            CalcLineItem(
                unit_price=procedures[item.procedure_id].price,
                quantity=item.quantity,
                unit_cost_estimated=procedures[item.procedure_id].estimated_cost,
                # Dia 1: nenhuma sessão aconteceu ainda -> custo realizado
                # = custo provisionado (uma "sessão virtual" por
                # unidade, todas com o custo estimado do procedimento).
                session_costs=[procedures[item.procedure_id].estimated_cost]
                * item.quantity,
            )
            for item in dto.items
        ]

        params = SaleParams(
            split_clinic_percentage=settings.split_clinic_percentage,
            split_base=CalcSplitBase(settings.split_base.value),
            fee_payer=CalcFeePayer(settings.fee_payer.value),
            payment_method=CalcPaymentMethod(dto.payment_method.value),
            installments=dto.installments,
            discount_amount=money(dto.discount_amount),
            fee_rules=fee_rules,
        )

        result = calculate_sale(calc_items, params)

        # Invariante I4 (MVP v6 §3): trunca no fuso da profissional, NUNCA
        # em UTC — uma venda às 22h em São Paulo (01h UTC do dia seguinte)
        # tem que valer para "hoje" dela, senão o erro aparece exatamente
        # no fechamento do dia, quando ela mais confere o número.
        professional = self._professionals.get_current()
        sold_at = today_in_timezone(professional.timezone)
        expected_receipt = expected_receipt_date(
            CalcPaymentMethod(dto.payment_method.value), sold_at, dto.installments
        )

        sale = Sale(
            patient_id=dto.patient_id,
            type=dto.type,
            sold_at=sold_at,
            status=SaleStatus.ACTIVE,
            payment_method=dto.payment_method,
            installments=dto.installments,
            items_total=result.items_total,
            discount_amount=result.discount_amount,
            gross_amount=result.gross_amount,
            split_applied=result.split_rate,
            split_amount_applied=result.split_amount,
            split_base_applied=settings.split_base,
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

        self._sales.flush()
        return sale

    def get(self, sale_id: UUID) -> Sale:
        sale = self._sales.get(sale_id)
        if sale is None:
            raise SaleNotFoundError()
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


def _snapshot_payload(
    result: SaleCalculationResult, settings
) -> dict:
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
