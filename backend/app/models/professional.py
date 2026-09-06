import secrets
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.models.base import Base, TimestampMixin


def _generate_weekly_summary_token() -> str:
    return secrets.token_urlsafe(32)


class Professional(Base, TimestampMixin):
    """A profissional é o tenant. professional_id em TenantModel aponta
    para esta tabela — não confundir com User (identidade de login).

    timezone é obrigatório (invariante I4): todo agrupamento por dia/mês
    converte para este fuso antes de truncar, senão uma venda das 21h em
    São Paulo aparece no dia seguinte em UTC.
    """

    __tablename__ = "professionals"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    clinic_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True
    )
    name: Mapped[str] = mapped_column(nullable=False)
    phone: Mapped[str | None] = mapped_column(nullable=True)
    timezone: Mapped[str] = mapped_column(
        default=settings.DEFAULT_TIMEZONE, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    slug: Mapped[str | None] = mapped_column(unique=True, index=True, nullable=True)
    bio: Mapped[str | None] = mapped_column(nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    specialty: Mapped[str | None] = mapped_column(String(120), nullable=True)
    weekly_summary_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    weekly_summary_token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        default=_generate_weekly_summary_token,
    )

