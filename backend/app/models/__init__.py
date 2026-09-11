"""Importa todos os modelos para que Base.metadata os conheça
(necessário para Alembic autogenerate e para os testes de arquitetura)."""

# Registra o listener before_flush que bloqueia UPDATE em campos
# congelados (T-020b, invariante I3) — importar por efeito colateral.
from app.models import listeners  # noqa: F401,E402
from app.models.anamnesis import (
    AnamnesisQuestion,
    AnamnesisSubmission,
    AnamnesisTemplate,
    QuestionFieldType,
)
from app.models.base import Base, TenantModel, TimestampMixin
from app.models.booking import Booking, BookingStatus
from app.models.clinic import Clinic
from app.models.financial_settings import (
    FeePayer,
    FinancialSettings,
    PaymentMethod,
    SplitBase,
)
from app.models.fixed_expense import ExpensePeriodicity, FixedExpense
from app.models.patient import Patient
from app.models.patient_photo import PatientPhoto, PhotoType
from app.models.payment_fee_rule import PaymentFeeRule
from app.models.procedure import Modality, Procedure, ProcedureType
from app.models.procedure_supply import ProcedureSupply
from app.models.professional import Professional
from app.models.return_opportunity import (
    ContactChannel,
    ReturnOpportunity,
    ReturnOpportunityStatus,
)
from app.models.sale import Sale, SaleStatus, SaleType
from app.models.sale_item import SaleItem
from app.models.session import Session, SessionStatus
from app.models.supply import (
    MovementType,
    Supply,
    SupplyCategory,
    SupplyMovement,
)
from app.models.campaign import CampaignTemplate
from app.models.coupon import Coupon
from app.models.loyalty import LoyaltyTransaction, LoyaltyTransactionType
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.terms_acceptance import TermsAcceptance
from app.models.user import User
from app.models.vial import OpenVial, VialStatus

__all__ = [
    "Base",
    "TenantModel",
    "TimestampMixin",
    "Clinic",
    "Subscription",
    "SubscriptionStatus",
    "Coupon",
    "User",
    "Supply",
    "SupplyCategory",
    "SupplyMovement",
    "MovementType",
    "Professional",
    "Patient",
    "PatientPhoto",
    "PhotoType",
    "OpenVial",
    "VialStatus",
    "Procedure",
    "ProcedureSupply",
    "ProcedureType",
    "Modality",
    "FinancialSettings",
    "SplitBase",
    "FeePayer",
    "PaymentMethod",
    "PaymentFeeRule",
    "FixedExpense",
    "ExpensePeriodicity",
    "Sale",
    "SaleType",
    "SaleStatus",
    "SaleItem",
    "Session",
    "SessionStatus",
    "ReturnOpportunity",
    "ReturnOpportunityStatus",
    "ContactChannel",
    "Booking",
    "BookingStatus",
    "TermsAcceptance",
    "CampaignTemplate",
    "LoyaltyTransaction",
    "LoyaltyTransactionType",
    "AnamnesisTemplate",
    "AnamnesisQuestion",
    "AnamnesisSubmission",
    "QuestionFieldType",
]
