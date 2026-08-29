"""Importa todos os modelos para que Base.metadata os conheça
(necessário para Alembic autogenerate e para os testes de arquitetura)."""

from app.models.base import Base, TenantModel, TimestampMixin
from app.models.patient import Patient
from app.models.procedure import Procedure, ProcedureType
from app.models.professional import Professional
from app.models.user import User

__all__ = [
    "Base",
    "TenantModel",
    "TimestampMixin",
    "User",
    "Professional",
    "Patient",
    "Procedure",
    "ProcedureType",
]
