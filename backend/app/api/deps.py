"""Dependency chain: JWT -> tenant -> sessão.

É impossível obter uma DbSession sem antes ter passado pela validação
do JWT — não existe caminho no código que produza sessão sem tenant.
Rotas públicas (/health) simplesmente não declaram DbSession.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_professional_id
from app.db.session import get_tenant_session, unsafe_session_without_tenant
from app.models.user import User
from app.repositories.booking import BookingRepository
from app.repositories.clinic import ClinicRepository
from app.repositories.financial_settings import FinancialSettingsRepository
from app.repositories.fixed_expense import FixedExpenseRepository
from app.repositories.patient import PatientRepository
from app.repositories.payment_fee_rule import PaymentFeeRuleRepository
from app.repositories.procedure import ProcedureRepository
from app.repositories.professional import ProfessionalRepository
from app.repositories.return_opportunity import ReturnOpportunityRepository
from app.repositories.sale import SaleRepository
from app.repositories.sale_item import SaleItemRepository
from app.repositories.session import SessionRepository
from app.repositories.user import UserRepository
from app.services.attribution_service import AttributionService
from app.services.booking_service import BookingService
from app.services.clinic_service import ClinicService
from app.services.dashboard_service import DashboardService
from app.services.export_service import ExportService
from app.services.financial_settings_service import FinancialSettingsService
from app.services.fixed_expense_service import FixedExpenseService
from app.services.patient_service import PatientService
from app.services.payment_fee_rule_service import PaymentFeeRuleService
from app.services.procedure_ranking_service import ProcedureRankingService
from app.services.procedure_service import ProcedureService
from app.services.retention_service import RetentionService
from app.services.sale_service import SaleService
from app.services.session_service import SessionService
from app.services.system_service import SystemService
from app.services.user_service import UserService

CurrentProfessional = Annotated[UUID, Depends(get_current_professional_id)]


def _db(professional_id: CurrentProfessional):
    yield from get_tenant_session(professional_id)


DbSession = Annotated[Session, Depends(_db)]


def _system_db():
    with unsafe_session_without_tenant("system status or setup") as session:
        yield session


SystemDbSession = Annotated[Session, Depends(_system_db)]


def get_current_user(
    session: DbSession, professional_id: CurrentProfessional
) -> User:
    user = UserRepository(session).get_by_id(professional_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> User:
    if user.role not in ("admin", "superadmin") and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return user


def require_superadmin(user: CurrentUser) -> User:
    if user.role != "superadmin" and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao Super Admin",
        )
    return user


AdminUser = Annotated[User, Depends(require_admin)]
SuperAdminUser = Annotated[User, Depends(require_superadmin)]
GlobalSuperAdminUser = Annotated[User, Depends(require_superadmin)]


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
        booking_repo=BookingRepository(session, professional_id),
        return_opportunity_repo=ReturnOpportunityRepository(session, professional_id),
    )


def get_session_service(
    session: DbSession, professional_id: CurrentProfessional
) -> SessionService:
    return SessionService(
        session_repo=SessionRepository(session, professional_id),
        sale_item_repo=SaleItemRepository(session, professional_id),
        sale_repo=SaleRepository(session, professional_id),
        procedure_repo=ProcedureRepository(session, professional_id),
        patient_repo=PatientRepository(session, professional_id),
        booking_repo=BookingRepository(session, professional_id),
        return_opportunity_repo=ReturnOpportunityRepository(session, professional_id),
        professional_repo=ProfessionalRepository(session, professional_id),
    )


def get_retention_service(
    session: DbSession, professional_id: CurrentProfessional
) -> RetentionService:
    return RetentionService(
        return_opportunity_repo=ReturnOpportunityRepository(session, professional_id),
        patient_repo=PatientRepository(session, professional_id),
        procedure_repo=ProcedureRepository(session, professional_id),
        professional_repo=ProfessionalRepository(session, professional_id),
    )


def get_booking_service(
    session: DbSession, professional_id: CurrentProfessional
) -> BookingService:
    return BookingService(
        booking_repo=BookingRepository(session, professional_id),
        session_repo=SessionRepository(session, professional_id),
        patient_repo=PatientRepository(session, professional_id),
        professional_repo=ProfessionalRepository(session, professional_id),
    )


def get_user_service(session: DbSession) -> UserService:
    return UserService(UserRepository(session))


def get_system_service(session: SystemDbSession) -> SystemService:
    return SystemService(UserRepository(session), session)


def get_clinic_service(session: DbSession) -> ClinicService:
    return ClinicService(ClinicRepository(session))


def get_system_clinic_service(session: SystemDbSession) -> ClinicService:
    return ClinicService(ClinicRepository(session))


def get_system_user_service(session: SystemDbSession) -> UserService:
    return UserService(UserRepository(session))


def get_attribution_service(
    session: DbSession, professional_id: CurrentProfessional
) -> AttributionService:
    return AttributionService(
        opportunity_repo=ReturnOpportunityRepository(session, professional_id),
        professional_repo=ProfessionalRepository(session, professional_id),
    )


def get_export_service(
    session: DbSession, professional_id: CurrentProfessional
) -> ExportService:
    return ExportService(
        patient_repo=PatientRepository(session, professional_id),
        sale_repo=SaleRepository(session, professional_id),
        session_repo=SessionRepository(session, professional_id),
        procedure_repo=ProcedureRepository(session, professional_id),
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
SessionSvc = Annotated[SessionService, Depends(get_session_service)]
RetentionSvc = Annotated[RetentionService, Depends(get_retention_service)]
BookingSvc = Annotated[BookingService, Depends(get_booking_service)]
UserSvc = Annotated[UserService, Depends(get_user_service)]
SystemSvc = Annotated[SystemService, Depends(get_system_service)]
ClinicSvc = Annotated[ClinicService, Depends(get_clinic_service)]
SystemClinicSvc = Annotated[ClinicService, Depends(get_system_clinic_service)]
SystemUserSvc = Annotated[UserService, Depends(get_system_user_service)]
AttributionSvc = Annotated[AttributionService, Depends(get_attribution_service)]
ExportSvc = Annotated[ExportService, Depends(get_export_service)]

