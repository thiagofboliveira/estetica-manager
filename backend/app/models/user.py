"""User — espelho de auth.users do Supabase.

Sem password_hash: a fonte de verdade de identidade é o Supabase Auth.
O backend valida JWT (app/core/security.py), nunca emite nem armazena
senha. Ver MVP v6 §7 e ../../ENGENHARIA.md invariante I2.
"""

from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    # Mesmo id do auth.users do Supabase — não gerado aqui.
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    clinic_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    role: Mapped[str] = mapped_column(default="user", nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
