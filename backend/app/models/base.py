"""Bases de modelo compartilhadas.

TenantModel garante professional_id não-nulo em toda tabela de tenant —
é a primeira das três camadas de defesa de isolamento (ver
../../ENGENHARIA.md, invariante I2). As outras duas são o
TenantRepository (repositories/base.py) e a policy de RLS no banco.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TenantModel(Base, TimestampMixin):
    """Base de toda tabela isolada por profissional.

    professional_id é FK com ondelete=RESTRICT: o banco recusa deletar
    um Professional que ainda tem dados filhos, e recusa inserir uma
    linha órfã de tenant.
    """

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    professional_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("professionals.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
