"""Event — tabela append-only de eventos de ativação (G-13).

Ver docs/pending/BACKLOG_GO_LIVE.md G-13/G-14. "Um sistema que não se
mede não pode ser melhorado" (docs/pending/BACKLOG_VERSAO_COMPLETA.md
princípio de produto #3) — o produto media o ROI da profissional com
rigor e não media nada de si mesmo.

Escopo desta versão: só a metade tenant-scoped (professional_id, RLS
igual às demais 11 tabelas de tenant). A visão cross-clínica do
super-admin (funil agregado entre TODAS as clínicas, V4-03 do
BACKLOG_VERSAO_COMPLETA.md) fica de fora de propósito — exigiria o
mesmo modelo de bypass de RLS por clinic_id que S-02 já identificou como
arriscado para implementar sem supervisão, e events não deveria ser o
primeiro lugar a testar isso.

Sem UPDATE nem DELETE por design — nenhum repository expõe esses
métodos. Um evento é um fato imutável do que aconteceu.
"""

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantModel


class Event(TenantModel):
    __tablename__ = "events"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    # Nome curto e estável — ver EventName em domain/events.py para o
    # catálogo fechado de nomes válidos (evita string solta espalhada
    # pelo código, que é impossível de auditar depois).
    name: Mapped[str] = mapped_column(nullable=False, index=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
