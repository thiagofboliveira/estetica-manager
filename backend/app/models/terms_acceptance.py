"""TermsAcceptance — Auditoria imutável de aceite de Termos de Uso e DPA/LGPD (G-10)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TermsAcceptance(Base):
    __tablename__ = "terms_acceptances"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    terms_version: Mapped[str] = mapped_column(String(32), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    accepted_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
