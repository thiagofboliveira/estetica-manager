"""Dependency chain: JWT -> tenant -> sessão.

É impossível obter uma DbSession sem antes ter passado pela validação
do JWT — não existe caminho no código que produza sessão sem tenant.
Rotas públicas (/health) simplesmente não declaram DbSession.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_professional_id
from app.db.session import get_tenant_session
from app.repositories.financial_settings import FinancialSettingsRepository
from app.repositories.fixed_expense import FixedExpenseRepository
from app.repositories.patient import PatientRepository
from app.repositories.payment_fee_rule import PaymentFeeRuleRepository
from app.repositories.procedure import ProcedureRepository
from app.repositories.professional import ProfessionalRepository
from app.repositories.sale import SaleRepository
from app.repositories.sale_item import SaleItemRepository
from app.repositories.session import SessionRepository
from app.services.dashboard_service import DashboardService
from app.services.financial_settings_service import FinancialSettingsService
from app.services.fixed_expense_service import FixedExpenseService
from app.services.patient_service import PatientService
from app.services.payment_fee_rule_service import PaymentFeeRuleService
from app.services.procedure_ranking_service import ProcedureRankingService
from app.services.procedure_service import ProcedureService
from app.services.sale_service import SaleService

CurrentProfessional = Annotated[UUID, Depends(get_current_professional_id)]


def _db(professional_id: CurrentProfessional):
    yield from get_tenant_session(professional_id)


DbSession = Annotated[Session, Depends(_db)]


def get_patient_service(
    session: DbSession, professional_id: CurrentProfessional
) -> PatientService:
    return PatientService(PatientRepository(session, professional_id))


def get_procedure_service(
    session: DbSession, professional_id: CurrentProfessional
) -> ProcedureService:
    return ProcedureService(ProcedureRepository(session, professional_id))


def get_financial_settings_service(
    session: DbSession, professional_id: CurrentProfessional
) -> FinancialSettingsService:
    return FinancialSettingsService(
        FinancialSettingsRepository(session, professional_id)
    )


def get_payment_fee_rule_service(
    session: DbSession, professional_id: CurrentProfessional
) -> PaymentFeeRuleService:
    return PaymentFeeRuleService(PaymentFeeRuleRepository(session, professional_id))


def get_fixed_expense_service(
    session: DbSession, professional_id: CurrentProfessional
) -> FixedExpenseService:
    return FixedExpenseService(FixedExpenseRepository(session, professional_id))


def get_dashboard_service(
    session: DbSession, professional_id: CurrentProfessional
) -> DashboardService:
    return DashboardService(
        sale_repo=SaleRepository(session, professional_id),
        session_repo=SessionRepository(session, professional_id),
        fixed_expense_repo=FixedExpenseRepository(session, professional_id),
        professional_repo=ProfessionalRepository(session, professional_id),
    )


def get_procedure_ranking_service(
    session: DbSession, professional_id: CurrentProfessional
) -> ProcedureRankingService:
    return ProcedureRankingService(
        sale_item_repo=SaleItemRepository(session, professional_id),
        procedure_repo=ProcedureRepository(session, professional_id),
        professional_repo=ProfessionalRepository(session, professional_id),
    )


def get_sale_service(
    session: DbSession, professional_id: CurrentProfessional
) -> SaleService:
    return SaleService(
        sale_repo=SaleRepository(session, professional_id),
        sale_item_repo=SaleItemRepository(session, professional_id),
        session_repo=SessionRepository(session, professional_id),
        procedure_repo=ProcedureRepository(session, professional_id),
        patient_repo=PatientRepository(session, professional_id),
        financial_settings_repo=FinancialSettingsRepository(session, professional_id),
        payment_fee_rule_repo=PaymentFeeRuleRepository(session, professional_id),
        professional_repo=ProfessionalRepository(session, professional_id),
    )


PatientSvc = Annotated[PatientService, Depends(get_patient_service)]
ProcedureSvc = Annotated[ProcedureService, Depends(get_procedure_service)]
FinancialSettingsSvc = Annotated[
    FinancialSettingsService, Depends(get_financial_settings_service)
]
PaymentFeeRuleSvc = Annotated[
    PaymentFeeRuleService, Depends(get_payment_fee_rule_service)
]
FixedExpenseSvc = Annotated[FixedExpenseService, Depends(get_fixed_expense_service)]
SaleSvc = Annotated[SaleService, Depends(get_sale_service)]
DashboardSvc = Annotated[DashboardService, Depends(get_dashboard_service)]
ProcedureRankingSvc = Annotated[
    ProcedureRankingService, Depends(get_procedure_ranking_service)
]
