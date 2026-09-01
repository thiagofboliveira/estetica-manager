from uuid import UUID, uuid4

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.models.base import Base, TimestampMixin


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
