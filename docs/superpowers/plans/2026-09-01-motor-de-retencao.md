# Motor de Retenção (T-025..T-031 + T-016) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the retention engine — `return_opportunities` table, the session-completion trigger that creates opportunities, the sale-time rule that closes them, and the two read/write endpoints the frontend needs (`GET /retention/opportunities`, `PATCH /retention/opportunities/{id}`) — plus the minimal `PATCH /sessions/{id}` endpoint (T-016) needed to ever reach `COMPLETED` in the first place.

**Architecture:** Pure domain layer (`app/domain/retention/`, no SQLAlchemy/FastAPI) for the state machine and window math → `ReturnOpportunityRepository`/`SessionRepository` extension for tenant-scoped queries → `RetentionService` for orchestration (creation-on-exhaustion, closing-on-sale) → thin API routers. Mirrors the existing `session_state_machine.py` / `SaleService` pattern exactly.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 (sync), Alembic, Pydantic v2, pytest, Postgres 16 (RLS).

**Spec:** [docs/superpowers/specs/2026-09-01-motor-de-retencao-design.md](../specs/2026-09-01-motor-de-retencao-design.md)

## Global Constraints

- Money fields: `Decimal`, `Numeric(12,2, asdecimal=True)` in models, `MoneyOut` in output schemas (serializes as JSON string, never number).
- Every tenant table subclasses `TenantModel` (`app/models/base.py`) — `professional_id` non-null, FK `ondelete=RESTRICT`.
- Child tables referencing another tenant table use a **composite FK** `(fk_column, professional_id) -> (parent.id, parent.professional_id)`, which requires the parent to have `UniqueConstraint(id, professional_id)`.
- All reads go through `TenantRepository._scoped()` — never a raw `session.query()`/`select()` outside a repository (enforced by `tests/test_architecture.py` + ruff banned-api).
- Domain code (`app/domain/**`) never imports SQLAlchemy, FastAPI, `app.models`, or `app.schemas` (enforced by `tests/test_architecture.py::test_dominio_nao_importa_infraestrutura`).
- Input schemas subclass `InputSchema` (`extra="forbid"`, never accept `professional_id` from the client — enforced by `tests/test_schemas_sem_tenant.py`).
- State transitions always go through a `validate_transition()` call before any UPDATE — never trust the caller.
- Timezone: any "today"/"now" used for business logic must use the professional's timezone (`app/core/tz.py`), never naive UTC truncation (invariant I4).
- RLS: every new table gets `ENABLE ROW LEVEL SECURITY`, `FORCE ROW LEVEL SECURITY`, and a `FOR ALL` policy on `professional_id = current_setting('app.professional_id', true)::uuid` for both `USING` and `WITH CHECK`.
- Migrations are written by hand (no live Postgres for autogenerate in dev) and must be manually cross-checked against the SQLAlchemy models before being applied.

---

### Task 1: `now_in_timezone()` helper + `ReturnOpportunityStatus` state machine (pure domain)

**Files:**
- Modify: `app/core/tz.py` (add `now_in_timezone`)
- Create: `app/domain/retention/__init__.py` (empty)
- Create: `app/domain/retention/return_opportunity_state_machine.py`
- Test: `app/core/tz.py` already has no dedicated test file — add coverage inline in the new domain test file's setup instead (see Task 2), skip a separate test for this 3-line helper.
- Test: `tests/test_return_opportunity_state_machine.py`

**Interfaces:**
- Produces: `app.core.tz.now_in_timezone(tz_name: str) -> datetime` (aware, in the given zone).
- Produces: `app.domain.retention.return_opportunity_state_machine.ReturnOpportunityStatus` (StrEnum: `OPEN, CONTACTED, BOOKED, DECLINED, NO_RESPONSE, DISMISSED, CLOSED`), `RETURN_OPPORTUNITY_TRANSITIONS` (`MappingProxyType[ReturnOpportunityStatus, frozenset[ReturnOpportunityStatus]]`), `InvalidReturnOpportunityTransitionError(current, target)`, `validate_transition(current, target) -> None`.

- [ ] **Step 1: Add `now_in_timezone` to `app/core/tz.py`**

```python
def now_in_timezone(tz_name: str) -> datetime:
    """O instante "agora" no fuso da profissional, aware — usar para
    carimbar completed_at/contacted_at, nunca datetime.now(UTC) direto
    (mesma disciplina de today_in_timezone, invariante I4)."""
    return datetime.now(ZoneInfo(tz_name))
```

(`datetime` and `ZoneInfo` are already imported in that file.)

- [ ] **Step 2: Write the failing test for the state machine**

Create `tests/test_return_opportunity_state_machine.py`:

```python
import pytest

from app.domain.retention.return_opportunity_state_machine import (
    RETURN_OPPORTUNITY_TRANSITIONS,
    InvalidReturnOpportunityTransitionError,
    ReturnOpportunityStatus,
    validate_transition,
)


def test_todo_status_esta_na_tabela():
    assert set(RETURN_OPPORTUNITY_TRANSITIONS) == set(ReturnOpportunityStatus)


@pytest.mark.parametrize(
    "current,target",
    [
        (ReturnOpportunityStatus.OPEN, ReturnOpportunityStatus.CONTACTED),
        (ReturnOpportunityStatus.OPEN, ReturnOpportunityStatus.DISMISSED),
        (ReturnOpportunityStatus.CONTACTED, ReturnOpportunityStatus.BOOKED),
        (ReturnOpportunityStatus.CONTACTED, ReturnOpportunityStatus.DECLINED),
        (ReturnOpportunityStatus.CONTACTED, ReturnOpportunityStatus.NO_RESPONSE),
        (ReturnOpportunityStatus.NO_RESPONSE, ReturnOpportunityStatus.CONTACTED),
        (ReturnOpportunityStatus.BOOKED, ReturnOpportunityStatus.CLOSED),
        (ReturnOpportunityStatus.DECLINED, ReturnOpportunityStatus.CLOSED),
    ],
)
def test_transicoes_validas_nao_levantam(current, target):
    validate_transition(current, target)  # não deve levantar


@pytest.mark.parametrize(
    "current,target",
    [
        (ReturnOpportunityStatus.OPEN, ReturnOpportunityStatus.BOOKED),
        (ReturnOpportunityStatus.OPEN, ReturnOpportunityStatus.CLOSED),
        (ReturnOpportunityStatus.CLOSED, ReturnOpportunityStatus.OPEN),
        (ReturnOpportunityStatus.DISMISSED, ReturnOpportunityStatus.OPEN),
        (ReturnOpportunityStatus.BOOKED, ReturnOpportunityStatus.CONTACTED),
    ],
)
def test_transicoes_invalidas_levantam(current, target):
    with pytest.raises(InvalidReturnOpportunityTransitionError):
        validate_transition(current, target)


def test_transicao_para_o_mesmo_status_e_no_op():
    validate_transition(ReturnOpportunityStatus.OPEN, ReturnOpportunityStatus.OPEN)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_return_opportunity_state_machine.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.domain.retention'`

- [ ] **Step 4: Implement the state machine**

Create `app/domain/retention/__init__.py` (empty file).

Create `app/domain/retention/return_opportunity_state_machine.py`:

```python
"""Máquina de estados de ReturnOpportunity (MVP v7.1 §14, TASK-025).

PURO: sem SQLAlchemy, sem FastAPI, sem app.models (mesma disciplina de
app.domain.sales.session_state_machine — ver
tests/test_architecture.py::test_dominio_nao_importa_infraestrutura).

Eixo de STATUS (persistido, movido por evento) — distinto do eixo de
TIMING (UPCOMING/DUE/OVERDUE, derivado de due_date vs hoje, nunca
persistido — ver app.domain.retention.window):

    OPEN --> CONTACTED
    OPEN --> DISMISSED
    CONTACTED --> BOOKED
    CONTACTED --> DECLINED
    CONTACTED --> NO_RESPONSE
    NO_RESPONSE --> CONTACTED : nova tentativa
    BOOKED --> CLOSED
    DECLINED --> CLOSED
    DISMISSED --> [*]
    CLOSED --> [*]

CLOSED é alcançado tanto por um evento manual da profissional (BOOKED/
DECLINED -> CLOSED) quanto pelo fechamento automático na venda (T-028,
RetentionService.close_open_opportunities) — este último pode fechar
diretamente de OPEN/CONTACTED/NO_RESPONSE para CLOSED, o que a tabela de
transições abaixo já permite adicionando essas arestas.
"""

from enum import StrEnum
from types import MappingProxyType


class ReturnOpportunityStatus(StrEnum):
    OPEN = "OPEN"
    CONTACTED = "CONTACTED"
    BOOKED = "BOOKED"
    DECLINED = "DECLINED"
    NO_RESPONSE = "NO_RESPONSE"
    DISMISSED = "DISMISSED"
    CLOSED = "CLOSED"


RETURN_OPPORTUNITY_TRANSITIONS: MappingProxyType[
    ReturnOpportunityStatus, frozenset[ReturnOpportunityStatus]
] = MappingProxyType(
    {
        ReturnOpportunityStatus.OPEN: frozenset(
            {
                ReturnOpportunityStatus.CONTACTED,
                ReturnOpportunityStatus.DISMISSED,
                ReturnOpportunityStatus.CLOSED,  # fechamento automático na venda (T-028)
            }
        ),
        ReturnOpportunityStatus.CONTACTED: frozenset(
            {
                ReturnOpportunityStatus.BOOKED,
                ReturnOpportunityStatus.DECLINED,
                ReturnOpportunityStatus.NO_RESPONSE,
                ReturnOpportunityStatus.CLOSED,  # fechamento automático na venda (T-028)
            }
        ),
        ReturnOpportunityStatus.NO_RESPONSE: frozenset(
            {
                ReturnOpportunityStatus.CONTACTED,
                ReturnOpportunityStatus.CLOSED,  # fechamento automático na venda (T-028)
            }
        ),
        ReturnOpportunityStatus.BOOKED: frozenset({ReturnOpportunityStatus.CLOSED}),
        ReturnOpportunityStatus.DECLINED: frozenset({ReturnOpportunityStatus.CLOSED}),
        ReturnOpportunityStatus.DISMISSED: frozenset(),  # terminal
        ReturnOpportunityStatus.CLOSED: frozenset(),  # terminal
    }
)


class InvalidReturnOpportunityTransitionError(Exception):
    def __init__(
        self, current: ReturnOpportunityStatus, target: ReturnOpportunityStatus
    ) -> None:
        self.current = current
        self.target = target
        super().__init__(f"transição inválida: {current} -> {target}")


def validate_transition(
    current: ReturnOpportunityStatus, target: ReturnOpportunityStatus
) -> None:
    """Levanta InvalidReturnOpportunityTransitionError se a transição não
    é permitida. Chamado pelo service antes de qualquer UPDATE — nunca
    confie que o chamador já validou."""
    if target == current:
        return
    allowed = RETURN_OPPORTUNITY_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise InvalidReturnOpportunityTransitionError(current, target)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_return_opportunity_state_machine.py -v`
Expected: PASS (all cases)

- [ ] **Step 6: Commit**

```bash
git add app/core/tz.py app/domain/retention/__init__.py app/domain/retention/return_opportunity_state_machine.py tests/test_return_opportunity_state_machine.py
git commit -m "feat(retention): add ReturnOpportunityStatus state machine + now_in_timezone"
```

---

### Task 2: Window calculation (pure domain)

**Files:**
- Create: `app/domain/retention/window.py`
- Test: `tests/test_retention_window.py`

**Interfaces:**
- Consumes: nothing (pure `date`/`timedelta` math).
- Produces: `app.domain.retention.window.Timing` (StrEnum: `UPCOMING, DUE, OVERDUE`), `calculate_due_date(completed_at: date, return_interval_days: int) -> date`, `classify_timing(due_date: date, today: date) -> Timing`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_retention_window.py`:

```python
from datetime import date

from app.domain.retention.window import Timing, calculate_due_date, classify_timing


def test_calculate_due_date_soma_intervalo_em_dias():
    assert calculate_due_date(date(2026, 3, 1), 180) == date(2026, 8, 28)


def test_calculate_due_date_intervalo_zero():
    assert calculate_due_date(date(2026, 3, 1), 0) == date(2026, 3, 1)


def test_classify_timing_upcoming_quando_falta_mais_de_7_dias():
    assert classify_timing(date(2026, 9, 20), today=date(2026, 9, 1)) == Timing.UPCOMING


def test_classify_timing_due_na_borda_superior_7_dias():
    assert classify_timing(date(2026, 9, 8), today=date(2026, 9, 1)) == Timing.DUE


def test_classify_timing_due_na_borda_inferior_menos_7_dias():
    assert classify_timing(date(2026, 8, 25), today=date(2026, 9, 1)) == Timing.DUE


def test_classify_timing_due_no_dia_exato():
    assert classify_timing(date(2026, 9, 1), today=date(2026, 9, 1)) == Timing.DUE


def test_classify_timing_overdue_quando_passou_de_7_dias():
    assert classify_timing(date(2026, 8, 24), today=date(2026, 9, 1)) == Timing.OVERDUE
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_retention_window.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.domain.retention.window'`

- [ ] **Step 3: Implement**

Create `app/domain/retention/window.py`:

```python
"""Cálculo da janela de retorno (MVP v7.1 §11.6, §14, TASK-026).

PURO: sem SQLAlchemy, sem FastAPI (mesma disciplina de
app.domain.financial.calculator).

due_date = última sessão COMPLETED do item + return_interval_applied
(§11.6) — decisão consciente de contar a partir da ÚLTIMA sessão
realizada, não da primeira nem da data da venda.

timing é derivado de due_date vs hoje EM TODA LEITURA, nunca persistido
— muda sozinho com o tempo, ao contrário de status (evento). Janela de
±7 dias em torno de due_date é "DUE"; fora dela é UPCOMING (futuro) ou
OVERDUE (passado)."""

from datetime import date, timedelta
from enum import StrEnum

_DUE_WINDOW_DAYS = 7


class Timing(StrEnum):
    UPCOMING = "UPCOMING"
    DUE = "DUE"
    OVERDUE = "OVERDUE"


def calculate_due_date(completed_at: date, return_interval_days: int) -> date:
    return completed_at + timedelta(days=return_interval_days)


def classify_timing(due_date: date, today: date) -> Timing:
    delta_days = (due_date - today).days
    if delta_days > _DUE_WINDOW_DAYS:
        return Timing.UPCOMING
    if delta_days < -_DUE_WINDOW_DAYS:
        return Timing.OVERDUE
    return Timing.DUE
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_retention_window.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/domain/retention/window.py tests/test_retention_window.py
git commit -m "feat(retention): add due_date/timing pure calculation"
```

---

### Task 3: `return_opportunities` model + migration

**Files:**
- Create: `app/models/return_opportunity.py`
- Create: `alembic/versions/0005_return_opportunities.py`
- Modify: `app/models/session.py` (no code change needed — `completed_at` already exists; this task only adds the missing index via migration)

**Interfaces:**
- Consumes: `app.domain.retention.return_opportunity_state_machine.ReturnOpportunityStatus` (Task 1).
- Produces: `app.models.return_opportunity.ReturnOpportunity` (SQLAlchemy model) with columns: `id, professional_id, patient_id, procedure_id, source_sale_item_id, due_date (date), potential_value (Decimal), status (ReturnOpportunityStatus), contacted_at (datetime|None), contact_channel (ContactChannel|None), resolved_by_sale_id (UUID|None), dismissed_at (datetime|None), created_at, updated_at`. Also produces `app.models.return_opportunity.ContactChannel` (StrEnum: `WHATSAPP, PHONE, IN_PERSON, OTHER`).

- [ ] **Step 1: Write the model**

Create `app/models/return_opportunity.py`:

```python
"""ReturnOpportunity — motor de retorno (MVP v7.1 §11.6, §14, TASK-025).

Nasce quando um sale_item se ESGOTA (nenhuma sessão PENDING/SCHEDULED/
CONFIRMED restante e ao menos uma COMPLETED) — não a cada sessão. Um
pacote de 10 limpezas gera UMA oportunidade, não dez (ver
RetentionService.check_and_create_opportunity).

potential_value é congelado de (sale_item.unit_price * quantity) na
criação — mesma disciplina de snapshot de sales/sale_items (invariante
I3): não muda se o preço do procedimento mudar depois.

Duas dimensões independentes:
  - status: persistido, movido por evento (ver
    app.domain.retention.return_opportunity_state_machine).
  - timing (UPCOMING/DUE/OVERDUE): NUNCA persistido, calculado em toda
    leitura a partir de due_date vs hoje (ver
    app.domain.retention.window) — por isso não há coluna aqui.

resolved_by_sale_id é preenchido pelo fechamento automático na venda
(T-028, RetentionService.close_open_opportunities) — nunca por edição
manual. Índice parcial garante no máximo uma oportunidade ATIVA (status
!= CLOSED) por source_sale_item_id, preservando histórico de
oportunidades fechadas.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Enum, ForeignKeyConstraint, Numeric
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.retention.return_opportunity_state_machine import (
    ReturnOpportunityStatus,
)
from app.models.base import TenantModel

__all__ = ["ReturnOpportunity", "ReturnOpportunityStatus", "ContactChannel"]


class ContactChannel(StrEnum):
    WHATSAPP = "WHATSAPP"
    PHONE = "PHONE"
    IN_PERSON = "IN_PERSON"
    OTHER = "OTHER"


class ReturnOpportunity(TenantModel):
    __tablename__ = "return_opportunities"
    __table_args__ = (
        ForeignKeyConstraint(
            ["patient_id", "professional_id"],
            ["patients.id", "patients.professional_id"],
            name="fk_return_opportunities_patient",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["procedure_id", "professional_id"],
            ["procedures.id", "procedures.professional_id"],
            name="fk_return_opportunities_procedure",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["source_sale_item_id", "professional_id"],
            ["sale_items.id", "sale_items.professional_id"],
            name="fk_return_opportunities_source_sale_item",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["resolved_by_sale_id", "professional_id"],
            ["sales.id", "sales.professional_id"],
            name="fk_return_opportunities_resolved_by_sale",
            ondelete="RESTRICT",
        ),
    )

    patient_id: Mapped[PGUUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )
    procedure_id: Mapped[PGUUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )
    source_sale_item_id: Mapped[PGUUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )
    due_date: Mapped[date] = mapped_column(nullable=False)
    potential_value: Mapped[Decimal] = mapped_column(
        Numeric(12, 2, asdecimal=True), nullable=False
    )
    status: Mapped[ReturnOpportunityStatus] = mapped_column(
        Enum(
            ReturnOpportunityStatus,
            name="return_opportunity_status",
            native_enum=False,
        ),
        nullable=False,
        default=ReturnOpportunityStatus.OPEN,
    )
    contacted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    contact_channel: Mapped[ContactChannel | None] = mapped_column(
        Enum(ContactChannel, name="contact_channel", native_enum=False),
        nullable=True,
    )
    resolved_by_sale_id: Mapped[PGUUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    dismissed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
```

- [ ] **Step 2: Write the migration**

Create `alembic/versions/0005_return_opportunities.py`:

```python
"""return_opportunities + índice de sessions.completed_at + RLS

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-01

⚠️ Gerada manualmente (sem acesso de rede a Postgres neste ambiente de
dev). Revisar contra app/models/return_opportunity.py antes de aplicar.

Cobre T-025 (MVP v7.1 §14, EPIC-10). patients e procedures não tinham
UniqueConstraint(id, professional_id) até agora (nenhuma tabela
referenciava elas via FK composta) — esta migration adiciona antes de
criar return_opportunities, que referencia as duas.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_patients_id_professional", "patients", ["id", "professional_id"]
    )
    op.create_unique_constraint(
        "uq_procedures_id_professional", "procedures", ["id", "professional_id"]
    )

    status = postgresql.ENUM(
        "OPEN",
        "CONTACTED",
        "BOOKED",
        "DECLINED",
        "NO_RESPONSE",
        "DISMISSED",
        "CLOSED",
        name="return_opportunity_status",
        create_type=False,
    )
    status.create(op.get_bind(), checkfirst=True)

    contact_channel = postgresql.ENUM(
        "WHATSAPP",
        "PHONE",
        "IN_PERSON",
        "OTHER",
        name="contact_channel",
        create_type=False,
    )
    contact_channel.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "return_opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "professional_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("professionals.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("procedure_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "source_sale_item_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("potential_value", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", status, nullable=False, server_default="OPEN"),
        sa.Column("contacted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("contact_channel", contact_channel, nullable=True),
        sa.Column(
            "resolved_by_sale_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("dismissed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["patient_id", "professional_id"],
            ["patients.id", "patients.professional_id"],
            name="fk_return_opportunities_patient",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["procedure_id", "professional_id"],
            ["procedures.id", "procedures.professional_id"],
            name="fk_return_opportunities_procedure",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_sale_item_id", "professional_id"],
            ["sale_items.id", "sale_items.professional_id"],
            name="fk_return_opportunities_source_sale_item",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by_sale_id", "professional_id"],
            ["sales.id", "sales.professional_id"],
            name="fk_return_opportunities_resolved_by_sale",
            ondelete="RESTRICT",
        ),
    )
    op.create_index(
        "ix_return_opportunities_professional_id",
        "return_opportunities",
        ["professional_id"],
    )
    op.create_index(
        "ix_return_opportunities_patient_id", "return_opportunities", ["patient_id"]
    )
    op.create_index(
        "ix_return_opportunities_procedure_id",
        "return_opportunities",
        ["procedure_id"],
    )
    op.create_index(
        "ix_return_opportunities_source_sale_item_id",
        "return_opportunities",
        ["source_sale_item_id"],
    )
    # Query de listagem (§20.4): filtra/ordena por due_date dentro de um
    # tenant, geralmente excluindo status terminal.
    op.create_index(
        "ix_return_opportunities_professional_due_status",
        "return_opportunities",
        ["professional_id", "due_date", "status"],
    )
    # No máximo uma oportunidade ATIVA por item-fonte — histórico de
    # oportunidades fechadas (CLOSED) não compete com uma nova aberta
    # para o mesmo item (não deveria acontecer na prática, mas a
    # constraint documenta e garante a invariante).
    op.create_index(
        "uq_return_opportunities_source_sale_item_active",
        "return_opportunities",
        ["source_sale_item_id"],
        unique=True,
        postgresql_where=sa.text("status != 'CLOSED'"),
    )

    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON return_opportunities TO estetica_app"
    )
    op.execute("ALTER TABLE return_opportunities ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE return_opportunities FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON return_opportunities
          FOR ALL TO estetica_app
          USING      (professional_id = current_setting('app.professional_id', true)::uuid)
          WITH CHECK (professional_id = current_setting('app.professional_id', true)::uuid)
        """
    )

    # §20.4 — índice que faltava para a busca de "última sessão COMPLETED
    # de um item" (window.calculate_due_date) e para contagem por
    # período (já usado por count_completed_in_period).
    op.create_index(
        "ix_sessions_professional_completed_at",
        "sessions",
        ["professional_id", "completed_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_sessions_professional_completed_at", table_name="sessions")
    op.drop_table("return_opportunities")
    op.execute("DROP TYPE IF EXISTS contact_channel")
    op.execute("DROP TYPE IF EXISTS return_opportunity_status")
    op.drop_constraint(
        "uq_procedures_id_professional", "procedures", type_="unique"
    )
    op.drop_constraint("uq_patients_id_professional", "patients", type_="unique")
```

- [ ] **Step 3: Verify the migration applies against a real Postgres**

Run: `.venv/bin/alembic upgrade head` (requires `docker-compose.dev.yml` Postgres running, per existing project setup)
Expected: migration `0005` applies with no errors.

- [ ] **Step 4: Verify schema with psql**

Run: `psql "$DATABASE_URL_MIGRATIONS" -c '\d return_opportunities'`
Expected: shows all columns, the 4 FK constraints, `Policies (forced row security enabled)`.

- [ ] **Step 5: Commit**

```bash
git add app/models/return_opportunity.py alembic/versions/0005_return_opportunities.py
git commit -m "feat(retention): add return_opportunities table + RLS (T-025)"
```

---

### Task 4: `ReturnOpportunityRepository` + `SessionRepository` extensions

**Files:**
- Create: `app/repositories/return_opportunity.py`
- Modify: `app/repositories/session.py` (add `list_for_sale_item` is already there; add nothing new — confirmed in Task 5 this is sufficient)
- Test: `tests/test_return_opportunity_repository.py` — **skip a dedicated unit test file**; repository methods are exercised end-to-end by the integration tests in Task 7 (matches the existing codebase convention: no repo has its own isolated test file, they're proven through the service/API integration tests, e.g. `SaleItemRepository`/`SessionRepository` have no dedicated test files).

**Interfaces:**
- Consumes: `app.models.return_opportunity.ReturnOpportunity` (Task 3), `app.domain.retention.return_opportunity_state_machine.ReturnOpportunityStatus` (Task 1).
- Produces: `ReturnOpportunityRepository(TenantRepository[ReturnOpportunity])` with methods:
  - `find_active_for_sale_item(sale_item_id: UUID) -> ReturnOpportunity | None`
  - `list_open_or_contacted_for_patient_and_procedure(patient_id: UUID, procedure_id: UUID) -> list[ReturnOpportunity]`
  - `list_non_terminal() -> list[ReturnOpportunity]`

- [ ] **Step 1: Implement the repository**

Create `app/repositories/return_opportunity.py`:

```python
"""ReturnOpportunityRepository (MVP v7.1 §14, TASK-025/028/029)."""

from uuid import UUID

from app.domain.retention.return_opportunity_state_machine import (
    ReturnOpportunityStatus,
)
from app.models.return_opportunity import ReturnOpportunity
from app.repositories.base import TenantRepository

_NON_TERMINAL = (
    ReturnOpportunityStatus.OPEN,
    ReturnOpportunityStatus.CONTACTED,
    ReturnOpportunityStatus.NO_RESPONSE,
)


class ReturnOpportunityRepository(TenantRepository[ReturnOpportunity]):
    model = ReturnOpportunity

    def find_active_for_sale_item(
        self, sale_item_id: UUID
    ) -> ReturnOpportunity | None:
        """Índice parcial único garante no máximo 1 linha não-CLOSED por
        item — usado para não duplicar oportunidade ao reprocessar
        exaustão (RetentionService.check_and_create_opportunity)."""
        stmt = self._scoped().where(
            ReturnOpportunity.source_sale_item_id == sale_item_id,
            ReturnOpportunity.status != ReturnOpportunityStatus.CLOSED,
        )
        return self._session.scalars(stmt).one_or_none()

    def list_open_or_contacted_for_patient_and_procedure(
        self, patient_id: UUID, procedure_id: UUID
    ) -> list[ReturnOpportunity]:
        """Base do fechamento automático na venda (T-028) — inclui
        NO_RESPONSE porque uma paciente que não respondeu ainda tem a
        oportunidade "em aberto" do ponto de vista de negócio."""
        stmt = self._scoped().where(
            ReturnOpportunity.patient_id == patient_id,
            ReturnOpportunity.procedure_id == procedure_id,
            ReturnOpportunity.status.in_(_NON_TERMINAL),
        )
        return list(self._session.scalars(stmt))

    def list_non_terminal(self) -> list[ReturnOpportunity]:
        """Base de GET /retention/opportunities (T-029/T-030) — DISMISSED
        e CLOSED nunca aparecem na tela de reativação."""
        stmt = self._scoped().where(
            ReturnOpportunity.status.in_(_NON_TERMINAL)
        )
        return list(self._session.scalars(stmt))
```

- [ ] **Step 2: Sanity-check imports**

Run: `.venv/bin/python -c "from app.repositories.return_opportunity import ReturnOpportunityRepository"`
Expected: no error.

- [ ] **Step 3: Commit**

```bash
git add app/repositories/return_opportunity.py
git commit -m "feat(retention): add ReturnOpportunityRepository"
```

---

### Task 5: `RetentionService` — creation-on-exhaustion + closing-on-sale

**Files:**
- Create: `app/services/retention_service.py`
- Test: `tests/test_retention_service_unit.py` (uses a fake/in-memory repo pair, no DB — mirrors how `session_state_machine` is unit-tested, but here we need to check the exhaustion logic which touches multiple sessions, so this is a lightweight service-level test using simple stub objects, not a live DB. Full DB-backed behavior is proven in Task 7's integration tests.)

**Interfaces:**
- Consumes: `ReturnOpportunityRepository` (Task 4), `SessionRepository.list_for_sale_item` (existing), `app.domain.retention.window.calculate_due_date` (Task 2), `app.domain.retention.return_opportunity_state_machine.validate_transition` (Task 1), `app.models.session.SessionStatus`.
- Produces:
  - `RetentionService.__init__(self, opportunity_repo: ReturnOpportunityRepository, session_repo: SessionRepository) -> None`
  - `RetentionService.check_and_create_opportunity(self, *, sale_item, professional_timezone: str) -> ReturnOpportunity | None` — `sale_item` is a `SaleItem` ORM object (has `.id`, `.sale_id` via join needed for `patient_id` — see note below), returns the created opportunity or `None` if the item isn't exhausted yet or already has an active opportunity.
  - `RetentionService.close_open_opportunities(self, *, patient_id: UUID, procedure_id: UUID, resolved_by_sale_id: UUID) -> None`

**Note on `patient_id`:** `SaleItem` has no direct `patient_id` column (it belongs to `Sale`, which has `patient_id`). `check_and_create_opportunity` must receive the `Sale` alongside the `SaleItem` to get `patient_id` — see the exact signature in Step 1.

- [ ] **Step 1: Write the failing unit test**

Create `tests/test_retention_service_unit.py`:

```python
"""Testes de RetentionService com repositórios reais contra um sale_item
já persistido — precisa de DB porque a exaustão consulta sessions reais
por sale_item_id. Roda contra Postgres real, mesmo padrão de
test_sales_integration.py (guardado pelo mesmo skipif)."""

import uuid
from datetime import date

import pytest

from app.core.config import settings
from app.domain.retention.return_opportunity_state_machine import (
    ReturnOpportunityStatus,
)
from app.models.patient import Patient
from app.models.procedure import Procedure, ProcedureType
from app.models.sale import Sale, SaleStatus, SaleType
from app.models.sale_item import SaleItem
from app.models.session import Session as SessionModel
from app.models.session import SessionStatus
from app.repositories.return_opportunity import ReturnOpportunityRepository
from app.repositories.session import SessionRepository
from app.services.retention_service import RetentionService

pytestmark = pytest.mark.skipif(
    not settings.DEV_AUTH_SECRET, reason="requer DEV_AUTH_SECRET + Postgres real"
)


@pytest.fixture
def professional_id(client):
    resp = client.post("/dev/login")
    return uuid.UUID(resp.json()["professional_id"])


def _build_sale_item(db_session, professional_id, *, quantity: int, interval_days: int | None):
    patient = Patient(name=f"Paciente {uuid.uuid4()}")
    patient.professional_id = professional_id
    db_session.add(patient)

    procedure = Procedure(
        name=f"Procedimento {uuid.uuid4()}",
        type=ProcedureType.SERVICE,
        price="100.00",
        estimated_cost="10.00",
        return_interval_days=interval_days,
    )
    procedure.professional_id = professional_id
    db_session.add(procedure)
    db_session.flush()

    sale = Sale(
        patient_id=patient.id,
        type=SaleType.PACKAGE,
        sold_at=date.today(),
        status=SaleStatus.ACTIVE,
        payment_method="PIX",
        installments=1,
        items_total="100.00",
        discount_amount="0.00",
        gross_amount="100.00",
        split_applied="0.0000",
        split_amount_applied="0.00",
        split_base_applied="GROSS",
        fee_payer_applied="PROFESSIONAL",
        fee_applied="0.0000",
        fee_amount_applied="0.00",
        fee_amount_charged_applied="0.00",
        cost_provisioned="10.00",
        cost_realized="10.00",
        net_profit="90.00",
        margin="0.9000",
    )
    sale.professional_id = professional_id
    db_session.add(sale)
    db_session.flush()

    sale_item = SaleItem(
        sale_id=sale.id,
        procedure_id=procedure.id,
        quantity=quantity,
        unit_price=procedure.price,
        unit_cost_estimated=procedure.estimated_cost,
        return_interval_applied=interval_days,
    )
    sale_item.professional_id = professional_id
    db_session.add(sale_item)
    db_session.flush()
    return sale, sale_item


def test_esgota_cria_oportunidade_com_due_date_da_ultima_completed(db_session, professional_id):
    sale, sale_item = _build_sale_item(
        db_session, professional_id, quantity=1, interval_days=180
    )
    session = SessionModel(
        sale_item_id=sale_item.id,
        sequence_number=1,
        status=SessionStatus.COMPLETED,
        modality="IN_PERSON",
        completed_at="2026-03-01T10:00:00+00:00",
    )
    session.professional_id = professional_id
    db_session.add(session)
    db_session.flush()

    svc = RetentionService(
        ReturnOpportunityRepository(db_session, professional_id),
        SessionRepository(db_session, professional_id),
    )
    opportunity = svc.check_and_create_opportunity(
        sale_item=sale_item, patient_id=sale.patient_id, professional_timezone="UTC"
    )

    assert opportunity is not None
    assert opportunity.status == ReturnOpportunityStatus.OPEN
    assert opportunity.due_date == date(2026, 8, 28)
    assert opportunity.potential_value == sale_item.unit_price * sale_item.quantity


def test_nao_esgotado_com_sessao_pending_nao_cria_oportunidade(db_session, professional_id):
    sale, sale_item = _build_sale_item(
        db_session, professional_id, quantity=2, interval_days=180
    )
    completed = SessionModel(
        sale_item_id=sale_item.id,
        sequence_number=1,
        status=SessionStatus.COMPLETED,
        modality="IN_PERSON",
        completed_at="2026-03-01T10:00:00+00:00",
    )
    completed.professional_id = professional_id
    pending = SessionModel(
        sale_item_id=sale_item.id,
        sequence_number=2,
        status=SessionStatus.PENDING,
        modality="IN_PERSON",
    )
    pending.professional_id = professional_id
    db_session.add_all([completed, pending])
    db_session.flush()

    svc = RetentionService(
        ReturnOpportunityRepository(db_session, professional_id),
        SessionRepository(db_session, professional_id),
    )
    opportunity = svc.check_and_create_opportunity(
        sale_item=sale_item, patient_id=sale.patient_id, professional_timezone="UTC"
    )

    assert opportunity is None


def test_procedimento_sem_intervalo_nunca_cria_oportunidade(db_session, professional_id):
    sale, sale_item = _build_sale_item(
        db_session, professional_id, quantity=1, interval_days=None
    )
    session = SessionModel(
        sale_item_id=sale_item.id,
        sequence_number=1,
        status=SessionStatus.COMPLETED,
        modality="IN_PERSON",
        completed_at="2026-03-01T10:00:00+00:00",
    )
    session.professional_id = professional_id
    db_session.add(session)
    db_session.flush()

    svc = RetentionService(
        ReturnOpportunityRepository(db_session, professional_id),
        SessionRepository(db_session, professional_id),
    )
    opportunity = svc.check_and_create_opportunity(
        sale_item=sale_item, patient_id=sale.patient_id, professional_timezone="UTC"
    )

    assert opportunity is None


def test_dez_sessoes_completadas_geram_uma_unica_oportunidade(db_session, professional_id):
    sale, sale_item = _build_sale_item(
        db_session, professional_id, quantity=10, interval_days=30
    )
    for seq in range(1, 11):
        session = SessionModel(
            sale_item_id=sale_item.id,
            sequence_number=seq,
            status=SessionStatus.COMPLETED,
            modality="IN_PERSON",
            completed_at="2026-03-01T10:00:00+00:00",
        )
        session.professional_id = professional_id
        db_session.add(session)
    db_session.flush()

    svc = RetentionService(
        ReturnOpportunityRepository(db_session, professional_id),
        SessionRepository(db_session, professional_id),
    )
    first = svc.check_and_create_opportunity(
        sale_item=sale_item, patient_id=sale.patient_id, professional_timezone="UTC"
    )
    second = svc.check_and_create_opportunity(
        sale_item=sale_item, patient_id=sale.patient_id, professional_timezone="UTC"
    )

    assert first is not None
    assert second is None  # já existe ativa para este source_sale_item_id


def test_close_open_opportunities_fecha_e_carimba_resolved_by_sale_id(db_session, professional_id):
    sale, sale_item = _build_sale_item(
        db_session, professional_id, quantity=1, interval_days=180
    )
    session = SessionModel(
        sale_item_id=sale_item.id,
        sequence_number=1,
        status=SessionStatus.COMPLETED,
        modality="IN_PERSON",
        completed_at="2026-03-01T10:00:00+00:00",
    )
    session.professional_id = professional_id
    db_session.add(session)
    db_session.flush()

    opportunity_repo = ReturnOpportunityRepository(db_session, professional_id)
    svc = RetentionService(opportunity_repo, SessionRepository(db_session, professional_id))
    opportunity = svc.check_and_create_opportunity(
        sale_item=sale_item, patient_id=sale.patient_id, professional_timezone="UTC"
    )
    assert opportunity is not None

    new_sale_id = uuid.uuid4()
    svc.close_open_opportunities(
        patient_id=sale.patient_id,
        procedure_id=sale_item.procedure_id,
        resolved_by_sale_id=new_sale_id,
    )
    db_session.flush()
    db_session.refresh(opportunity)

    assert opportunity.status == ReturnOpportunityStatus.CLOSED
    assert opportunity.resolved_by_sale_id == new_sale_id
```

(This test uses a `db_session`/`client` fixture — confirm the exact fixture names against `tests/conftest.py` before running; if the project's fixtures are named differently, e.g. `session` instead of `db_session`, adjust the test to match. This is the one place in the plan where the exact fixture name must be cross-checked against `tests/conftest.py` at execution time.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_retention_service_unit.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.retention_service'`

- [ ] **Step 3: Implement `RetentionService`**

Create `app/services/retention_service.py`:

```python
"""RetentionService — orquestra a criação (T-025/026/027) e o
fechamento (T-028) de return_opportunities.

Camada de orquestração (backend/ENGENHARIA.md §5): consulta sessions
reais, chama o domínio puro (window.calculate_due_date) e persiste. O
CÁLCULO da data em si vive em domain/ — testável sem banco.
"""

from uuid import UUID

from app.domain.retention.return_opportunity_state_machine import (
    ReturnOpportunityStatus,
    validate_transition,
)
from app.domain.retention.window import calculate_due_date
from app.domain.sales.session_state_machine import SessionStatus
from app.models.return_opportunity import ReturnOpportunity
from app.models.sale_item import SaleItem
from app.repositories.return_opportunity import ReturnOpportunityRepository
from app.repositories.session import SessionRepository

_NON_EXHAUSTING_STATUSES = (
    SessionStatus.PENDING,
    SessionStatus.SCHEDULED,
    SessionStatus.CONFIRMED,
)


class RetentionService:
    def __init__(
        self,
        opportunity_repo: ReturnOpportunityRepository,
        session_repo: SessionRepository,
    ) -> None:
        self._opportunities = opportunity_repo
        self._sessions = session_repo

    def check_and_create_opportunity(
        self,
        *,
        sale_item: SaleItem,
        patient_id: UUID,
        professional_timezone: str,
    ) -> ReturnOpportunity | None:
        """Chamado sempre que uma sessão do item muda de status (T-016).
        Cria a oportunidade apenas se: (1) o procedimento tem intervalo
        de retorno (produtos não têm — §9), (2) o item esgotou (nenhuma
        sessão PENDING/SCHEDULED/CONFIRMED restante), (3) existe ao
        menos uma sessão COMPLETED, (4) não existe já uma oportunidade
        ATIVA para este item (índice parcial único garante isso no
        banco; checar aqui evita round-trip de erro de constraint)."""
        if sale_item.return_interval_applied is None:
            return None

        if self._opportunities.find_active_for_sale_item(sale_item.id) is not None:
            return None

        sessions = self._sessions.list_for_sale_item(sale_item.id)
        if any(s.status in _NON_EXHAUSTING_STATUSES for s in sessions):
            return None

        completed = [s for s in sessions if s.status == SessionStatus.COMPLETED]
        if not completed:
            return None

        last_completed_at = max(s.completed_at for s in completed)
        due_date = calculate_due_date(
            last_completed_at.astimezone(
                __import__("zoneinfo").ZoneInfo(professional_timezone)
            ).date(),
            sale_item.return_interval_applied,
        )

        opportunity = ReturnOpportunity(
            patient_id=patient_id,
            procedure_id=sale_item.procedure_id,
            source_sale_item_id=sale_item.id,
            due_date=due_date,
            potential_value=sale_item.unit_price * sale_item.quantity,
            status=ReturnOpportunityStatus.OPEN,
        )
        return self._opportunities.add(opportunity)

    def close_open_opportunities(
        self,
        *,
        patient_id: UUID,
        procedure_id: UUID,
        resolved_by_sale_id: UUID,
    ) -> None:
        """Chamado por SaleService.create() (T-028) na mesma transação da
        nova venda — fecha toda oportunidade não-terminal do mesmo par
        (paciente, procedimento), atribuindo a venda que a resolveu."""
        opportunities = (
            self._opportunities.list_open_or_contacted_for_patient_and_procedure(
                patient_id, procedure_id
            )
        )
        for opportunity in opportunities:
            validate_transition(opportunity.status, ReturnOpportunityStatus.CLOSED)
            opportunity.status = ReturnOpportunityStatus.CLOSED
            opportunity.resolved_by_sale_id = resolved_by_sale_id
        self._opportunities.flush()
```

Replace the inline `__import__("zoneinfo")` with a proper top-level import for cleanliness:

```python
from zoneinfo import ZoneInfo
```

and use `last_completed_at.astimezone(ZoneInfo(professional_timezone)).date()`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_retention_service_unit.py -v`
Expected: PASS (all 5 cases)

- [ ] **Step 5: Commit**

```bash
git add app/services/retention_service.py tests/test_retention_service_unit.py
git commit -m "feat(retention): add RetentionService (creation on exhaustion, closing on sale)"
```

---

### Task 6: T-016 — `PATCH /sessions/{id}` (prerequisite trigger)

**Files:**
- Create: `app/schemas/session.py`
- Create: `app/api/v1/sessions.py`
- Modify: `app/api/deps.py` (add `SessionSvc`, wire `RetentionSvc` too since Task 8 needs it — do both here to avoid touching `deps.py` twice)
- Modify: `app/services/sale_service.py` (add a small `update_session_status` method — see Step 3)
- Modify: `app/main.py` (register the new router)
- Test: `tests/test_sessions_integration.py`

**Interfaces:**
- Consumes: `app.domain.sales.session_state_machine.validate_transition`, `RetentionService.check_and_create_opportunity` (Task 5).
- Produces: `PATCH /api/v1/sessions/{id}` accepting `{"status": "COMPLETED"}` (or any valid `SessionStatus` value), returning the updated session; wired end-to-end with retention-opportunity creation.
- Produces: `app.api.deps.SessionSvc`, `app.api.deps.RetentionSvc` type aliases and their `get_*_service` factories.

- [ ] **Step 1: Write the schema**

Create `app/schemas/session.py`:

```python
from datetime import datetime
from uuid import UUID

from app.domain.sales.session_state_machine import SessionStatus
from app.schemas.base import InputSchema, OutputSchema
from app.schemas.types import MoneyOut


class SessionUpdate(InputSchema):
    status: SessionStatus


class SessionDetailOut(OutputSchema):
    id: UUID
    sale_item_id: UUID
    sequence_number: int
    scheduled_at: datetime | None
    completed_at: datetime | None
    status: SessionStatus
    modality: str
    cost_override: MoneyOut | None
    notes: str | None
```

- [ ] **Step 2: Write the failing integration test**

Create `tests/test_sessions_integration.py`:

```python
"""T-016 — PATCH /sessions/{id}. Testado contra Postgres real, mesmo
padrão de test_sales_integration.py."""

import pytest

from app.core.config import settings

pytestmark = pytest.mark.skipif(
    not settings.DEV_AUTH_SECRET, reason="requer DEV_AUTH_SECRET + Postgres real"
)


@pytest.fixture
def auth_headers(client):
    resp = client.post("/dev/login")
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def patient_id(client, auth_headers):
    resp = client.post(
        "/api/v1/patients", json={"name": "Paciente Sessão"}, headers=auth_headers
    )
    return resp.json()["id"]


@pytest.fixture
def procedure_id(client, auth_headers):
    resp = client.post(
        "/api/v1/procedures",
        json={
            "name": "Procedimento Sessão",
            "price": "100.00",
            "estimated_cost": "10.00",
            "return_interval_days": 30,
        },
        headers=auth_headers,
    )
    return resp.json()["id"]


def test_patch_session_para_completed_seta_completed_at(
    client, auth_headers, patient_id, procedure_id
):
    sale_resp = client.post(
        "/api/v1/sales",
        json={
            "patient_id": patient_id,
            "type": "SINGLE",
            "items": [{"procedure_id": procedure_id, "quantity": 1}],
            "payment_method": "PIX",
        },
        headers=auth_headers,
    )
    session_id = sale_resp.json()["sessions"][0]["id"]

    resp = client.patch(
        f"/api/v1/sessions/{session_id}",
        json={"status": "COMPLETED"},
        headers=auth_headers,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "COMPLETED"
    assert body["completed_at"] is not None


def test_patch_session_transicao_invalida_retorna_409(
    client, auth_headers, patient_id, procedure_id
):
    sale_resp = client.post(
        "/api/v1/sales",
        json={
            "patient_id": patient_id,
            "type": "SINGLE",
            "items": [{"procedure_id": procedure_id, "quantity": 1}],
            "payment_method": "PIX",
        },
        headers=auth_headers,
    )
    session_id = sale_resp.json()["sessions"][0]["id"]
    client.patch(
        f"/api/v1/sessions/{session_id}",
        json={"status": "COMPLETED"},
        headers=auth_headers,
    )

    resp = client.patch(
        f"/api/v1/sessions/{session_id}",
        json={"status": "SCHEDULED"},
        headers=auth_headers,
    )

    assert resp.status_code == 409


def test_patch_session_inexistente_retorna_404(client, auth_headers):
    resp = client.patch(
        "/api/v1/sessions/00000000-0000-0000-0000-000000000000",
        json={"status": "COMPLETED"},
        headers=auth_headers,
    )
    assert resp.status_code == 404
```

- [ ] **Step 3: Add `update_session_status` to `SaleService` (or a dedicated small service — decision: dedicated `SessionService`, since this is session-scoped orchestration, not sale-scoped)**

Create the service inline in `app/api/v1/sessions.py`'s dependency, but to keep with the layering (route -> service -> repo), add a small service. Create `app/services/session_service.py`:

```python
"""SessionService — orquestra PATCH /sessions/{id} (T-016).

Camada fina: valida a transição via domain, persiste, e aciona a
checagem de exaustão do motor de retorno (T-025) na mesma transação.
"""

from uuid import UUID

from app.domain.sales.session_state_machine import SessionStatus, validate_transition
from app.models.session import Session as SessionModel
from app.repositories.sale_item import SaleItemRepository
from app.repositories.sale import SaleRepository
from app.repositories.session import SessionRepository
from app.services.retention_service import RetentionService


class SessionNotFoundError(Exception):
    pass


class SessionService:
    def __init__(
        self,
        session_repo: SessionRepository,
        sale_item_repo: SaleItemRepository,
        sale_repo: SaleRepository,
        retention_service: RetentionService,
        professional_timezone: str,
    ) -> None:
        self._sessions = session_repo
        self._sale_items = sale_item_repo
        self._sales = sale_repo
        self._retention = retention_service
        self._professional_timezone = professional_timezone

    def update_status(self, session_id: UUID, new_status: SessionStatus) -> SessionModel:
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError()

        validate_transition(session.status, new_status)
        session.status = new_status
        if new_status == SessionStatus.COMPLETED:
            from app.core.tz import now_in_timezone

            session.completed_at = now_in_timezone(self._professional_timezone)
        self._sessions.flush()

        sale_item = self._sale_items.get(session.sale_item_id)
        sale = self._sales.get(sale_item.sale_id)
        self._retention.check_and_create_opportunity(
            sale_item=sale_item,
            patient_id=sale.patient_id,
            professional_timezone=self._professional_timezone,
        )

        return session
```

Move the `from app.core.tz import now_in_timezone` to the top of the file instead of inline (inline import shown above only to keep the diff obvious — the actual file must import it at module level, consistent with the rest of the codebase's style):

```python
from app.core.tz import now_in_timezone
```

- [ ] **Step 4: Wire dependencies in `app/api/deps.py`**

Add these imports at the top (alongside existing ones):

```python
from app.repositories.return_opportunity import ReturnOpportunityRepository
from app.services.retention_service import RetentionService
from app.services.session_service import SessionService
```

Add these factory functions and type aliases at the end of the file:

```python
def get_retention_service(
    session: DbSession, professional_id: CurrentProfessional
) -> RetentionService:
    return RetentionService(
        ReturnOpportunityRepository(session, professional_id),
        SessionRepository(session, professional_id),
    )


def get_session_service(
    session: DbSession, professional_id: CurrentProfessional
) -> SessionService:
    professional = ProfessionalRepository(session, professional_id).get_current()
    return SessionService(
        SessionRepository(session, professional_id),
        SaleItemRepository(session, professional_id),
        SaleRepository(session, professional_id),
        get_retention_service(session, professional_id),
        professional.timezone,
    )


RetentionSvc = Annotated[RetentionService, Depends(get_retention_service)]
SessionSvc = Annotated[SessionService, Depends(get_session_service)]
```

- [ ] **Step 5: Write the route**

Create `app/api/v1/sessions.py`:

```python
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import SessionSvc
from app.schemas.session import SessionDetailOut, SessionUpdate
from app.services.session_service import SessionNotFoundError

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.patch("/{session_id}", response_model=SessionDetailOut)
def update_session(
    session_id: UUID, payload: SessionUpdate, svc: SessionSvc
) -> SessionDetailOut:
    try:
        session = svc.update_status(session_id, payload.status)
    except SessionNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Sessão não encontrada"
        ) from exc
    except Exception as exc:
        # InvalidSessionTransitionError — 409, mesma disciplina de
        # IdempotencyKeyConflictError em sales.py.
        from app.domain.sales.session_state_machine import (
            InvalidSessionTransitionError,
        )

        if isinstance(exc, InvalidSessionTransitionError):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"transição inválida: {exc.current} -> {exc.target}",
            ) from exc
        raise
    return SessionDetailOut.model_validate(session)
```

Clean up the `except Exception` catch-all into an explicit `except InvalidSessionTransitionError` (move the import to the top of the file):

```python
from app.domain.sales.session_state_machine import InvalidSessionTransitionError
```

and:

```python
    try:
        session = svc.update_status(session_id, payload.status)
    except SessionNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Sessão não encontrada"
        ) from exc
    except InvalidSessionTransitionError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"transição inválida: {exc.current} -> {exc.target}",
        ) from exc
    return SessionDetailOut.model_validate(session)
```

- [ ] **Step 6: Register the router in `app/main.py`**

Find the `from app.api.v1 import (...)` import block and add `sessions`; find the `app.include_router(...)` block and add:

```python
app.include_router(sessions.router, prefix="/api/v1")
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_sessions_integration.py -v`
Expected: PASS (all 3 cases)

- [ ] **Step 8: Commit**

```bash
git add app/schemas/session.py app/api/v1/sessions.py app/services/session_service.py app/api/deps.py app/main.py tests/test_sessions_integration.py
git commit -m "feat(sessions): add PATCH /sessions/{id} (T-016), triggers retention check"
```

---

### Task 7: Wire closing rule into `SaleService.create()` (T-028)

**Files:**
- Modify: `app/services/sale_service.py`
- Modify: `app/api/deps.py` (`get_sale_service` needs `RetentionService` + professional timezone)
- Test: `tests/test_retention_integration.py` (full-cycle integration test, T-045/T-045a/T-045b)

**Interfaces:**
- Consumes: `RetentionService.close_open_opportunities` (Task 5), `RetentionService.check_and_create_opportunity` (Task 5, already wired via `SessionService` in Task 6 — `SaleService` only needs closing, not creation, since a fresh sale's sessions start as `PENDING`/`SCHEDULED`, never `COMPLETED`).
- Produces: `SaleService.__init__` gains a `retention_service: RetentionService` parameter; `SaleService.create()` calls `close_open_opportunities` once per distinct `procedure_id` in the new sale, after the sale and its items/sessions are persisted, before the final `flush()`.

- [ ] **Step 1: Write the failing integration test**

Create `tests/test_retention_integration.py`:

```python
"""T-025..T-031, T-045/T-045a/T-045b — ciclo completo do motor de
retorno, testado contra Postgres real (mesmo padrão de
test_sales_integration.py)."""

import pytest

from app.core.config import settings

pytestmark = pytest.mark.skipif(
    not settings.DEV_AUTH_SECRET, reason="requer DEV_AUTH_SECRET + Postgres real"
)


@pytest.fixture
def auth_headers(client):
    resp = client.post("/dev/login")
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def patient_id(client, auth_headers):
    resp = client.post(
        "/api/v1/patients",
        json={"name": "Maria Retenção", "phone": "+5511987654321"},
        headers=auth_headers,
    )
    return resp.json()["id"]


def _create_procedure(client, auth_headers, *, interval_days: int):
    resp = client.post(
        "/api/v1/procedures",
        json={
            "name": "Botox Retenção",
            "price": "1000.00",
            "estimated_cost": "100.00",
            "return_interval_days": interval_days,
        },
        headers=auth_headers,
    )
    return resp.json()["id"]


def _sell_and_complete_single(client, auth_headers, patient_id, procedure_id):
    sale_resp = client.post(
        "/api/v1/sales",
        json={
            "patient_id": patient_id,
            "type": "SINGLE",
            "items": [{"procedure_id": procedure_id, "quantity": 1}],
            "payment_method": "PIX",
        },
        headers=auth_headers,
    )
    session_id = sale_resp.json()["sessions"][0]["id"]
    client.patch(
        f"/api/v1/sessions/{session_id}",
        json={"status": "COMPLETED"},
        headers=auth_headers,
    )
    return sale_resp.json()["id"]


def test_ciclo_completo_venda_completa_lista_contata_nova_venda_fecha(
    client, auth_headers, patient_id
):
    procedure_id = _create_procedure(client, auth_headers, interval_days=1)
    _sell_and_complete_single(client, auth_headers, patient_id, procedure_id)

    list_resp = client.get("/api/v1/retention/opportunities", headers=auth_headers)
    assert list_resp.status_code == 200
    patients = list_resp.json()
    target = next(p for p in patients if p["patient_id"] == patient_id)
    assert target["opportunities"][0]["status"] == "OPEN"
    opportunity_id = target["opportunities"][0]["id"]

    contact_resp = client.patch(
        f"/api/v1/retention/opportunities/{opportunity_id}",
        json={"status": "CONTACTED", "contact_channel": "WHATSAPP"},
        headers=auth_headers,
    )
    assert contact_resp.status_code == 200
    assert contact_resp.json()["status"] == "CONTACTED"

    new_sale_resp = client.post(
        "/api/v1/sales",
        json={
            "patient_id": patient_id,
            "type": "SINGLE",
            "items": [{"procedure_id": procedure_id, "quantity": 1}],
            "payment_method": "PIX",
        },
        headers=auth_headers,
    )
    new_sale_id = new_sale_resp.json()["id"]

    list_resp_after = client.get(
        "/api/v1/retention/opportunities", headers=auth_headers
    )
    remaining_patients = list_resp_after.json()
    assert not any(p["patient_id"] == patient_id for p in remaining_patients)


def test_pacote_com_sessao_pending_nao_aparece_na_lista(
    client, auth_headers, patient_id
):
    procedure_id = _create_procedure(client, auth_headers, interval_days=30)
    sale_resp = client.post(
        "/api/v1/sales",
        json={
            "patient_id": patient_id,
            "type": "PACKAGE",
            "items": [{"procedure_id": procedure_id, "quantity": 2}],
            "payment_method": "PIX",
        },
        headers=auth_headers,
    )
    sessions = sale_resp.json()["sessions"]
    client.patch(
        f"/api/v1/sessions/{sessions[0]['id']}",
        json={"status": "SCHEDULED"},
        headers=auth_headers,
    )
    client.patch(
        f"/api/v1/sessions/{sessions[0]['id']}",
        json={"status": "COMPLETED"},
        headers=auth_headers,
    )
    # sessions[1] continua PENDING — item não esgotou.

    list_resp = client.get("/api/v1/retention/opportunities", headers=auth_headers)
    patients = list_resp.json()
    assert not any(p["patient_id"] == patient_id for p in patients)


def test_pacote_de_dez_sessoes_gera_uma_unica_oportunidade(
    client, auth_headers, patient_id
):
    procedure_id = _create_procedure(client, auth_headers, interval_days=30)
    sale_resp = client.post(
        "/api/v1/sales",
        json={
            "patient_id": patient_id,
            "type": "PACKAGE",
            "items": [{"procedure_id": procedure_id, "quantity": 10}],
            "payment_method": "PIX",
        },
        headers=auth_headers,
    )
    sessions = sale_resp.json()["sessions"]
    for s in sessions:
        client.patch(
            f"/api/v1/sessions/{s['id']}",
            json={"status": "SCHEDULED"},
            headers=auth_headers,
        )
        client.patch(
            f"/api/v1/sessions/{s['id']}",
            json={"status": "COMPLETED"},
            headers=auth_headers,
        )

    list_resp = client.get("/api/v1/retention/opportunities", headers=auth_headers)
    target = next(p for p in list_resp.json() if p["patient_id"] == patient_id)
    assert len(target["opportunities"]) == 1
    assert target["opportunities"][0]["potential_value"] == "10000.00"
```

Note: `sessions[0]` above starts as `PENDING` (package) — `PATCH` to `SCHEDULED` first, then `COMPLETED`, since `PENDING -> COMPLETED` directly is not a valid transition (must go through `SCHEDULED` or `CONFIRMED` per `SESSION_TRANSITIONS`).

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_retention_integration.py -v`
Expected: FAIL — `GET /api/v1/retention/opportunities` returns 404 (route doesn't exist yet) and `SaleService` doesn't close opportunities yet.

- [ ] **Step 3: Modify `SaleService` to close opportunities on sale creation**

In `app/services/sale_service.py`, modify the constructor:

```python
    def __init__(
        self,
        sale_repo: SaleRepository,
        sale_item_repo: SaleItemRepository,
        session_repo: SessionRepository,
        procedure_repo: ProcedureRepository,
        patient_repo: PatientRepository,
        financial_settings_repo: FinancialSettingsRepository,
        payment_fee_rule_repo: PaymentFeeRuleRepository,
        professional_repo: ProfessionalRepository,
        retention_service: "RetentionService",
    ) -> None:
        self._sales = sale_repo
        self._sale_items = sale_item_repo
        self._sessions = session_repo
        self._procedures = procedure_repo
        self._patients = patient_repo
        self._financial_settings = financial_settings_repo
        self._payment_fee_rules = payment_fee_rule_repo
        self._professionals = professional_repo
        self._retention = retention_service
```

Add the import at the top of the file:

```python
from app.services.retention_service import RetentionService
```

(remove the string-quoted forward reference `"RetentionService"` in the constructor signature above and use the real import — the quoted form was only to show the diff inline; the actual type hint is `retention_service: RetentionService`.)

In `create()`, right after the `for item_dto, item_result in zip(...)` loop that creates `sale_item`/sessions (i.e., after the loop body finishes, still before `self._sales.flush()`), add the closing-rule call:

```python
        for procedure_id in {item_dto.procedure_id for item_dto in dto.items}:
            self._retention.close_open_opportunities(
                patient_id=dto.patient_id,
                procedure_id=procedure_id,
                resolved_by_sale_id=sale.id,
            )

        self._sales.flush()
        return sale
```

- [ ] **Step 4: Wire `RetentionService` into `get_sale_service` in `app/api/deps.py`**

Modify the existing `get_sale_service` function:

```python
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
        retention_service=get_retention_service(session, professional_id),
    )
```

(This requires `get_retention_service` — defined in Task 6, Step 4 — to appear *before* `get_sale_service` in the file, or Python will raise `NameError` at import time since both are module-level functions evaluated at call time, not definition time — function bodies are fine referencing a name defined later in the same module, so no reordering is actually required. Leave the existing function order as-is.)

- [ ] **Step 5: Run tests again**

Run: `.venv/bin/pytest tests/test_retention_integration.py -v`
Expected: Still FAIL — closing rule now wired, but `GET`/`PATCH /retention/opportunities` still don't exist (Task 8 covers that). This step confirms the failure mode changed (404 on the retention endpoints specifically, not an error in `SaleService`).

Run also the full sales test suite to confirm no regression from the constructor signature change:

Run: `.venv/bin/pytest tests/test_sales_integration.py tests/test_sale_calculator.py -v`
Expected: PASS (existing tests use `get_sale_service` via the API, not direct `SaleService()` construction, so they're unaffected — confirm this by checking `tests/test_sales_integration.py` doesn't instantiate `SaleService` directly; if it does, it also needs a `retention_service` argument added).

- [ ] **Step 6: Commit**

```bash
git add app/services/sale_service.py app/api/deps.py
git commit -m "feat(retention): close open opportunities when a matching sale is registered (T-028)"
```

---

### Task 8: `GET /retention/opportunities` + `PATCH /retention/opportunities/{id}` (T-029, T-030, T-031)

**Files:**
- Create: `app/schemas/retention.py`
- Create: `app/domain/retention/grouping.py` (pure: group-by-patient + suppression + sort)
- Create: `app/api/v1/retention.py`
- Modify: `app/main.py` (register router)
- Test: `tests/test_retention_grouping.py` (pure domain test)
- Test: `tests/test_retention_integration.py` (already created in Task 7 — this task makes those tests pass)

**Interfaces:**
- Consumes: `ReturnOpportunityRepository.list_non_terminal` (Task 4), `app.domain.retention.window.classify_timing` (Task 2), `app.core.tz.today_in_timezone` / `utc_to_local_date` (existing), `ReturnOpportunityStatus`/`validate_transition` (Task 1), `Patient` model fields `consent_whatsapp`, `opted_out_at`, `phone`.
- Produces:
  - `app.domain.retention.grouping.group_by_patient(opportunities: list[OpportunityForGrouping], *, today: date, suppression_days: int = 14) -> list[PatientRetentionGroup]` — pure function, takes a narrow dataclass cut (not ORM objects), mirroring the `dashboard.py` "narrow input cut" pattern.
  - `GET /api/v1/retention/opportunities` → `list[PatientRetentionOut]`
  - `PATCH /api/v1/retention/opportunities/{id}` → `ReturnOpportunityOut`

- [ ] **Step 1: Write the failing pure domain test for grouping**

Create `tests/test_retention_grouping.py`:

```python
from datetime import date, datetime, timedelta

from app.domain.retention.grouping import OpportunityForGrouping, group_by_patient


def _opp(**overrides):
    defaults = dict(
        id="opp-1",
        patient_id="pat-1",
        patient_name="Maria",
        patient_phone="+5511999999999",
        consent_whatsapp=True,
        opted_out_at=None,
        last_contacted_at=None,
        procedure_name="Botox",
        due_date=date(2026, 9, 1),
        status="OPEN",
        potential_value="1000.00",
    )
    defaults.update(overrides)
    return OpportunityForGrouping(**defaults)


def test_agrupa_por_paciente_um_card_por_paciente():
    opportunities = [
        _opp(id="a", patient_id="pat-1", potential_value="1000.00"),
        _opp(id="b", patient_id="pat-1", procedure_name="Skinbooster", potential_value="300.00"),
        _opp(id="c", patient_id="pat-2", potential_value="200.00"),
    ]
    groups = group_by_patient(opportunities, today=date(2026, 9, 1))
    assert len(groups) == 2
    maria = next(g for g in groups if g.patient_id == "pat-1")
    assert len(maria.opportunities) == 2
    assert maria.total_potential_value == "1300.00"


def test_ordena_por_atraso_mais_atrasado_primeiro():
    opportunities = [
        _opp(id="a", patient_id="pat-1", due_date=date(2026, 9, 10)),
        _opp(id="b", patient_id="pat-1", procedure_name="Skinbooster", due_date=date(2026, 8, 1)),
    ]
    groups = group_by_patient(opportunities, today=date(2026, 9, 1))
    assert groups[0].opportunities[0].procedure == "Skinbooster"


def test_ordena_pacientes_por_valor_potencial_total_decrescente():
    opportunities = [
        _opp(id="a", patient_id="pat-1", potential_value="100.00"),
        _opp(id="b", patient_id="pat-2", potential_value="900.00"),
    ]
    groups = group_by_patient(opportunities, today=date(2026, 9, 1))
    assert groups[0].patient_id == "pat-2"


def test_suprime_paciente_contatada_ha_menos_de_14_dias():
    opportunities = [
        _opp(
            patient_id="pat-1",
            last_contacted_at=datetime(2026, 8, 30, 12, 0),
        )
    ]
    groups = group_by_patient(opportunities, today=date(2026, 9, 1))
    assert groups == []


def test_nao_suprime_paciente_contatada_ha_mais_de_14_dias():
    opportunities = [
        _opp(
            patient_id="pat-1",
            last_contacted_at=datetime(2026, 8, 10, 12, 0),
        )
    ]
    groups = group_by_patient(opportunities, today=date(2026, 9, 1))
    assert len(groups) == 1


def test_can_contact_falso_sem_consentimento():
    opportunities = [_opp(patient_id="pat-1", consent_whatsapp=False)]
    groups = group_by_patient(opportunities, today=date(2026, 9, 1))
    assert groups[0].can_contact is False
    assert groups[0].cannot_contact_reason is not None


def test_can_contact_falso_sem_telefone():
    opportunities = [_opp(patient_id="pat-1", patient_phone=None)]
    groups = group_by_patient(opportunities, today=date(2026, 9, 1))
    assert groups[0].can_contact is False


def test_can_contact_falso_com_opt_out():
    opportunities = [
        _opp(patient_id="pat-1", opted_out_at=datetime(2026, 1, 1))
    ]
    groups = group_by_patient(opportunities, today=date(2026, 9, 1))
    assert groups[0].can_contact is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_retention_grouping.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.domain.retention.grouping'`

- [ ] **Step 3: Implement the pure grouping/suppression domain function**

Create `app/domain/retention/grouping.py`:

```python
"""Agrupamento e supressão da tela de reativação (MVP v7.1 §15,
TASK-030). PURO: recebe cortes estreitos de dados (dataclasses), nunca
SQLAlchemy — mesmo padrão de app.domain.financial.dashboard.

Um card por paciente, não por oportunidade (§15): 'return_interval_days
é por procedimento — Maria com Botox+Skinbooster+Limpeza apareceria três
vezes e receberia três disparos de WhatsApp na mesma semana'.
Supressão de 14 dias é por PACIENTE, independente de quantas
oportunidades ela tenha — aplicada aqui, não no service, para ficar
testável sem banco."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from app.domain.retention.window import Timing, classify_timing

_SUPPRESSION_DAYS = 14


@dataclass(frozen=True)
class OpportunityForGrouping:
    id: str
    patient_id: str
    patient_name: str
    patient_phone: str | None
    consent_whatsapp: bool
    opted_out_at: datetime | None
    last_contacted_at: datetime | None
    procedure_name: str
    due_date: date
    status: str
    potential_value: str


@dataclass(frozen=True)
class OpportunityLine:
    id: str
    procedure: str
    due_date: date
    timing: Timing
    status: str
    potential_value: str


@dataclass(frozen=True)
class PatientRetentionGroup:
    patient_id: str
    patient_name: str
    patient_phone: str | None
    can_contact: bool
    cannot_contact_reason: str | None
    total_potential_value: str
    opportunities: list[OpportunityLine]


def _cannot_contact_reason(opp: OpportunityForGrouping) -> str | None:
    if not opp.patient_phone:
        return "Paciente sem telefone cadastrado"
    if opp.opted_out_at is not None:
        return "Paciente optou por não receber mensagens"
    if not opp.consent_whatsapp:
        return "Paciente não deu consentimento para WhatsApp"
    return None


def group_by_patient(
    opportunities: list[OpportunityForGrouping],
    *,
    today: date,
    suppression_days: int = _SUPPRESSION_DAYS,
) -> list[PatientRetentionGroup]:
    by_patient: dict[str, list[OpportunityForGrouping]] = {}
    for opp in opportunities:
        by_patient.setdefault(opp.patient_id, []).append(opp)

    groups: list[PatientRetentionGroup] = []
    for patient_id, patient_opps in by_patient.items():
        last_contacted = next(
            (o.last_contacted_at for o in patient_opps if o.last_contacted_at),
            None,
        )
        if last_contacted is not None:
            days_since_contact = (today - last_contacted.date()).days
            if days_since_contact < suppression_days:
                continue

        sorted_opps = sorted(patient_opps, key=lambda o: o.due_date)
        lines = [
            OpportunityLine(
                id=o.id,
                procedure=o.procedure_name,
                due_date=o.due_date,
                timing=classify_timing(o.due_date, today),
                status=o.status,
                potential_value=o.potential_value,
            )
            for o in sorted_opps
        ]
        total = sum((Decimal(o.potential_value) for o in patient_opps), Decimal("0.00"))
        first = patient_opps[0]
        groups.append(
            PatientRetentionGroup(
                patient_id=patient_id,
                patient_name=first.patient_name,
                patient_phone=first.patient_phone,
                can_contact=all(_cannot_contact_reason(o) is None for o in patient_opps),
                cannot_contact_reason=_cannot_contact_reason(first),
                total_potential_value=str(total.quantize(Decimal("0.01"))),
                opportunities=lines,
            )
        )

    groups.sort(key=lambda g: Decimal(g.total_potential_value), reverse=True)
    return groups
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_retention_grouping.py -v`
Expected: PASS (all 8 cases)

- [ ] **Step 5: Commit the pure domain piece**

```bash
git add app/domain/retention/grouping.py tests/test_retention_grouping.py
git commit -m "feat(retention): add pure group-by-patient + suppression logic (T-030)"
```

- [ ] **Step 6: Add `list_non_terminal_with_details` to `ReturnOpportunityRepository`**

The repository method from Task 4 (`list_non_terminal`) returns bare `ReturnOpportunity` rows; the API needs patient name/phone/consent and procedure name too. Modify `app/repositories/return_opportunity.py` to add a joined query:

```python
from app.models.patient import Patient
from app.models.procedure import Procedure


class ReturnOpportunityRepository(TenantRepository[ReturnOpportunity]):
    # ... existing methods unchanged ...

    def list_non_terminal_with_details(
        self,
    ) -> list[tuple[ReturnOpportunity, Patient, Procedure]]:
        """Junta patient/procedure para a tela de reativação (T-029/030)
        — evita N+1 queries do lado do service."""
        stmt = (
            self._scoped()
            .where(ReturnOpportunity.status.in_(_NON_TERMINAL))
            .join(Patient, Patient.id == ReturnOpportunity.patient_id)
            .join(Procedure, Procedure.id == ReturnOpportunity.procedure_id)
            .add_columns(Patient, Procedure)
        )
        return [
            (opp, patient, procedure)
            for opp, patient, procedure in self._session.execute(stmt).all()
        ]
```

- [ ] **Step 7: Write the schemas**

Create `app/schemas/retention.py`:

```python
from datetime import date, datetime
from uuid import UUID

from app.models.return_opportunity import ContactChannel, ReturnOpportunityStatus
from app.schemas.base import InputSchema, OutputSchema
from app.schemas.types import MoneyOut


class OpportunityLineOut(OutputSchema):
    id: UUID
    procedure: str
    due_date: date
    timing: str
    status: ReturnOpportunityStatus
    potential_value: MoneyOut


class PatientRetentionOut(OutputSchema):
    patient_id: UUID
    patient_name: str
    patient_phone: str | None
    can_contact: bool
    cannot_contact_reason: str | None
    total_potential_value: MoneyOut
    opportunities: list[OpportunityLineOut]


class ReturnOpportunityUpdate(InputSchema):
    status: ReturnOpportunityStatus
    contact_channel: ContactChannel | None = None


class ReturnOpportunityOut(OutputSchema):
    id: UUID
    patient_id: UUID
    procedure_id: UUID
    due_date: date
    potential_value: MoneyOut
    status: ReturnOpportunityStatus
    contacted_at: datetime | None
    contact_channel: ContactChannel | None
    resolved_by_sale_id: UUID | None
    dismissed_at: datetime | None
```

- [ ] **Step 8: Add `get`, `update_status` to `RetentionService` for the API layer**

Modify `app/services/retention_service.py` — add these methods to `RetentionService`:

```python
    def get(self, opportunity_id):
        opportunity = self._opportunities.get(opportunity_id)
        if opportunity is None:
            raise ReturnOpportunityNotFoundError()
        return opportunity

    def list_for_reactivation_screen(
        self, *, today, professional_timezone: str
    ) -> list:
        from app.domain.retention.grouping import (
            OpportunityForGrouping,
            group_by_patient,
        )

        rows = self._opportunities.list_non_terminal_with_details()
        cuts = [
            OpportunityForGrouping(
                id=str(opp.id),
                patient_id=str(patient.id),
                patient_name=patient.name,
                patient_phone=patient.phone,
                consent_whatsapp=patient.consent_whatsapp,
                opted_out_at=patient.opted_out_at,
                last_contacted_at=opp.contacted_at,
                procedure_name=procedure.name,
                due_date=opp.due_date,
                status=opp.status.value,
                potential_value=str(opp.potential_value),
            )
            for opp, patient, procedure in rows
        ]
        return group_by_patient(cuts, today=today)

    def update_status(self, opportunity_id, new_status, contact_channel=None):
        from datetime import datetime as _datetime

        from zoneinfo import ZoneInfo

        opportunity = self.get(opportunity_id)
        validate_transition(opportunity.status, new_status)
        opportunity.status = new_status
        if new_status == ReturnOpportunityStatus.CONTACTED:
            opportunity.contacted_at = _datetime.now(ZoneInfo("UTC"))
            opportunity.contact_channel = contact_channel
        elif new_status == ReturnOpportunityStatus.DISMISSED:
            opportunity.dismissed_at = _datetime.now(ZoneInfo("UTC"))
        self._opportunities.flush()
        return opportunity
```

Clean up the inline imports — move `datetime` and `ZoneInfo` to the top of `app/services/retention_service.py` (they're likely already imported for `check_and_create_opportunity`'s `ZoneInfo` usage from Task 5; consolidate into one top-level `from datetime import datetime` and `from zoneinfo import ZoneInfo`). Also move `OpportunityForGrouping, group_by_patient` import to the top of the file instead of inline.

Add the exception class at the top of the file, alongside the class definition:

```python
class ReturnOpportunityNotFoundError(Exception):
    pass
```

Add explicit type hints matching the rest of the codebase's style:

```python
    def get(self, opportunity_id: UUID) -> ReturnOpportunity:
        ...

    def list_for_reactivation_screen(
        self, *, today: date, professional_timezone: str
    ) -> list["PatientRetentionGroup"]:
        ...

    def update_status(
        self,
        opportunity_id: UUID,
        new_status: ReturnOpportunityStatus,
        contact_channel: "ContactChannel | None" = None,
    ) -> ReturnOpportunity:
        ...
```

with the necessary imports added at the top: `from datetime import date`, `from app.models.return_opportunity import ContactChannel`, `from app.domain.retention.grouping import PatientRetentionGroup`.

- [ ] **Step 9: Write the route**

Create `app/api/v1/retention.py`:

```python
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import RetentionSvc
from app.core.tz import today_in_timezone
from app.domain.retention.return_opportunity_state_machine import (
    InvalidReturnOpportunityTransitionError,
)
from app.repositories.professional import ProfessionalRepository
from app.schemas.retention import (
    PatientRetentionOut,
    ReturnOpportunityOut,
    ReturnOpportunityUpdate,
)
from app.services.retention_service import ReturnOpportunityNotFoundError

router = APIRouter(prefix="/retention", tags=["retention"])


@router.get("/opportunities", response_model=list[PatientRetentionOut])
def list_opportunities(svc: RetentionSvc) -> list[PatientRetentionOut]:
    groups = svc.list_for_reactivation_screen(
        today=today_in_timezone("UTC"), professional_timezone="UTC"
    )
    return [PatientRetentionOut.model_validate(g) for g in groups]


@router.patch("/opportunities/{opportunity_id}", response_model=ReturnOpportunityOut)
def update_opportunity(
    opportunity_id: UUID, payload: ReturnOpportunityUpdate, svc: RetentionSvc
) -> ReturnOpportunityOut:
    try:
        opportunity = svc.update_status(
            opportunity_id, payload.status, payload.contact_channel
        )
    except ReturnOpportunityNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Oportunidade não encontrada"
        ) from exc
    except InvalidReturnOpportunityTransitionError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"transição inválida: {exc.current} -> {exc.target}",
        ) from exc
    return ReturnOpportunityOut.model_validate(opportunity)
```

**Fix the hardcoded `"UTC"` timezone**: `list_opportunities` must use the professional's real timezone (invariant I4), not a hardcoded value. Modify the route to inject the professional's timezone via a small dependency. Add to `app/api/deps.py`:

```python
def get_professional_timezone(
    session: DbSession, professional_id: CurrentProfessional
) -> str:
    return ProfessionalRepository(session, professional_id).get_current().timezone


ProfessionalTimezone = Annotated[str, Depends(get_professional_timezone)]
```

Update `app/api/v1/retention.py`'s import and route signature:

```python
from app.api.deps import ProfessionalTimezone, RetentionSvc


@router.get("/opportunities", response_model=list[PatientRetentionOut])
def list_opportunities(
    svc: RetentionSvc, timezone: ProfessionalTimezone
) -> list[PatientRetentionOut]:
    groups = svc.list_for_reactivation_screen(
        today=today_in_timezone(timezone), professional_timezone=timezone
    )
    return [PatientRetentionOut.model_validate(g) for g in groups]
```

Remove the now-unused `from app.repositories.professional import ProfessionalRepository` import from `retention.py` (it moved to `deps.py`).

- [ ] **Step 10: Register the router in `app/main.py`**

Add `retention` to the `from app.api.v1 import (...)` block and:

```python
app.include_router(retention.router, prefix="/api/v1")
```

- [ ] **Step 11: Run the full retention integration suite**

Run: `.venv/bin/pytest tests/test_retention_integration.py -v`
Expected: PASS (all 3 cases from Task 7)

- [ ] **Step 12: Run the complete backend test suite to check for regressions**

Run: `.venv/bin/pytest -q`
Expected: All tests pass (previous count was 133; this plan adds roughly 8 + 6 + 5 + 3 + 3 + 8 ≈ 33 new tests).

- [ ] **Step 13: Run ruff**

Run: `.venv/bin/ruff check .`
Expected: clean, no violations (in particular no raw `session.query()`/`select()` outside a repository, and no domain-layer import of infra).

- [ ] **Step 14: Commit**

```bash
git add app/schemas/retention.py app/api/v1/retention.py app/services/retention_service.py app/repositories/return_opportunity.py app/api/deps.py app/main.py
git commit -m "feat(retention): add GET/PATCH /retention/opportunities (T-029, T-030, T-031)"
```

---

### Task 9: Update `backend/BACKLOG.md`

**Files:**
- Modify: `backend/BACKLOG.md`

**Interfaces:** none — documentation only.

- [ ] **Step 1: Mark T-016, T-025, T-026, T-028, T-029, T-030, T-031 as `[x]` with evidence notes**

Edit the relevant rows in `backend/BACKLOG.md` (FASE 2 T-016 row, FASE 3 "Motor de retorno" table) following the file's existing convention (`**DONE exige evidência:** teste passando ou endpoint respondendo`), citing:
- Test files and counts (`tests/test_return_opportunity_state_machine.py`, `tests/test_retention_window.py`, `tests/test_retention_service_unit.py`, `tests/test_sessions_integration.py`, `tests/test_retention_grouping.py`, `tests/test_retention_integration.py`).
- Migration `0005_return_opportunities.py` applied and verified with `\d return_opportunities`.
- Update the "Atualizado" line and progress counter at the top of the file (was 54/86 — add the number of tasks now done: T-016, T-025, T-026, T-028, T-029, T-030, T-031 = 7 tasks, so 61/86).

Leave T-027 marked as already `[x]` (it was implemented earlier per the existing note in the file). Leave T-045/T-045a/T-045b as `[ ]` unless this plan's integration tests are considered to satisfy them — **decision: mark T-045, T-045a, T-045b as `[x]` too**, since `tests/test_retention_integration.py` directly covers all three (full cycle, PENDING suppression, 10-session package = 1 opportunity), bringing the total to 64/86.

- [ ] **Step 2: Commit**

```bash
git add backend/BACKLOG.md
git commit -m "docs: mark T-016, T-025, T-026, T-028..T-031, T-045..T-045b done"
```

---

## Post-plan notes for the executor

- **`tests/conftest.py` fixtures**: this plan assumes fixtures named `client` (a `TestClient`) and `db_session` exist or can be added following the exact pattern already used by `tests/test_sales_integration.py` and `tests/test_fixed_expenses_integration.py`. Before Task 5, Step 1, read `tests/conftest.py` and adjust fixture names in the new test files if they differ from what's assumed here (e.g., if there's no raw `db_session` fixture exposing the SQLAlchemy `Session`, add one following the same pattern as the `client` fixture, scoped to reuse the same tenant-scoped session as `get_tenant_session`).
- **`SaleType`/`SessionStatus` as strings in test payloads**: confirm the exact literal values accepted by `SaleCreate`/`SessionUpdate` schemas (`"SINGLE"`, `"PACKAGE"`, `"COMPLETED"`, etc.) against `app/models/sale.py`'s `SaleType` enum before running Task 6/7's integration tests — the plan uses the same string values already used in `tests/test_sales_integration.py`.
- **`ProfessionalTimezone` naming collision**: `app/api/deps.py` already exports many `*Svc` aliases; double-check `ProfessionalTimezone` doesn't collide with an existing name before adding it (a quick `grep -n "ProfessionalTimezone" app/api/deps.py` before Task 8 Step 9 confirms it's new).
