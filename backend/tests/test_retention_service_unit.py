"""Testes de RetentionService com stubs leves (sem DB, sem HTTP).

DESVIO DELIBERADO do plano original da task: o brief pedia testes de
integração com `db_session`/`client` reais (Patient/Procedure/Sale/
SaleItem/Session persistidos). Essa fixture `db_session` não existe
neste projeto — não há tests/conftest.py, e todo teste de integração
existente (test_sales_integration.py, test_fixed_expenses_integration.py)
constrói fixtures via chamadas HTTP reais (client + /dev/login), nunca
manipulando uma Session do SQLAlchemy diretamente.

Este arquivo testa apenas a lógica de branching do RetentionService
(exaustão, bloqueios, idempotência, fechamento) com objetos stub
(SimpleNamespace / fakes simples) no lugar de instâncias ORM reais e
com fakes dos dois repositórios. A prova com repositórios reais contra
Postgres fica para os testes de integração da Task 7, que exercitarão
este serviço via API HTTP completa assim que o endpoint de conclusão de
sessão (T-016) existir.
"""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.domain.retention.return_opportunity_state_machine import (
    InvalidReturnOpportunityTransitionError,
    ReturnOpportunityStatus,
)
from app.domain.sales.session_state_machine import SessionStatus
from app.services.retention_service import RetentionService


def _sale_item(*, quantity=1, unit_price=Decimal("100.00"), interval_days=180):
    return SimpleNamespace(
        id=uuid.uuid4(),
        procedure_id=uuid.uuid4(),
        unit_price=unit_price,
        quantity=quantity,
        return_interval_applied=interval_days,
    )


def _session(*, status, completed_at=None):
    return SimpleNamespace(status=status, completed_at=completed_at)


class FakeOpportunityRepository:
    """Fake de ReturnOpportunityRepository — registra chamadas e devolve
    dados canned em vez de bater no banco."""

    def __init__(self, *, active_for_sale_item=None, open_or_contacted=None):
        self._active_for_sale_item = active_for_sale_item
        self._open_or_contacted = open_or_contacted or []
        self.added: list = []
        self.find_active_for_sale_item_calls: list = []
        self.list_open_or_contacted_calls: list = []
        self.flush_calls = 0

    def find_active_for_sale_item(self, sale_item_id):
        self.find_active_for_sale_item_calls.append(sale_item_id)
        return self._active_for_sale_item

    def list_open_or_contacted_for_patient_and_procedure(
        self, patient_id, procedure_id
    ):
        self.list_open_or_contacted_calls.append((patient_id, procedure_id))
        return self._open_or_contacted

    def add(self, obj):
        self.added.append(obj)
        return obj

    def flush(self):
        self.flush_calls += 1


class FakeSessionRepository:
    """Fake de SessionRepository — devolve uma lista canned de sessions
    (stubs) para list_for_sale_item."""

    def __init__(self, sessions):
        self._sessions = sessions
        self.list_for_sale_item_calls: list = []

    def list_for_sale_item(self, sale_item_id):
        self.list_for_sale_item_calls.append(sale_item_id)
        return self._sessions


def test_esgota_cria_oportunidade_com_due_date_correto():
    sale_item = _sale_item(quantity=1, unit_price=Decimal("100.00"), interval_days=180)
    completed_at = datetime(2026, 3, 1, 10, 0, 0, tzinfo=UTC)
    session = _session(status=SessionStatus.COMPLETED, completed_at=completed_at)

    opp_repo = FakeOpportunityRepository(active_for_sale_item=None)
    session_repo = FakeSessionRepository([session])
    svc = RetentionService(opp_repo, session_repo)

    patient_id = uuid.uuid4()
    opportunity = svc.check_and_create_opportunity(
        sale_item=sale_item, patient_id=patient_id, professional_timezone="UTC"
    )

    assert opportunity is not None
    assert opportunity.status == ReturnOpportunityStatus.OPEN
    assert opportunity.due_date == date(2026, 8, 28)
    assert opportunity.potential_value == sale_item.unit_price * sale_item.quantity
    assert opportunity.patient_id == patient_id
    assert opportunity.procedure_id == sale_item.procedure_id
    assert opportunity.source_sale_item_id == sale_item.id
    assert opp_repo.added == [opportunity]


def test_sessao_pending_bloqueia_criacao():
    sale_item = _sale_item(quantity=2, interval_days=180)
    completed = _session(
        status=SessionStatus.COMPLETED,
        completed_at=datetime(2026, 3, 1, 10, 0, 0, tzinfo=UTC),
    )
    pending = _session(status=SessionStatus.PENDING)

    opp_repo = FakeOpportunityRepository()
    session_repo = FakeSessionRepository([completed, pending])
    svc = RetentionService(opp_repo, session_repo)

    opportunity = svc.check_and_create_opportunity(
        sale_item=sale_item, patient_id=uuid.uuid4(), professional_timezone="UTC"
    )

    assert opportunity is None
    assert opp_repo.added == []


def test_sem_return_interval_nunca_cria_oportunidade():
    sale_item = _sale_item(quantity=1, interval_days=None)
    completed = _session(
        status=SessionStatus.COMPLETED,
        completed_at=datetime(2026, 3, 1, 10, 0, 0, tzinfo=UTC),
    )

    opp_repo = FakeOpportunityRepository()
    session_repo = FakeSessionRepository([completed])
    svc = RetentionService(opp_repo, session_repo)

    opportunity = svc.check_and_create_opportunity(
        sale_item=sale_item, patient_id=uuid.uuid4(), professional_timezone="UTC"
    )

    assert opportunity is None
    # nem chega a consultar sessions — return_interval_applied é checado primeiro
    assert session_repo.list_for_sale_item_calls == []
    assert opp_repo.added == []


def test_ja_existe_oportunidade_ativa_nao_duplica():
    sale_item = _sale_item(quantity=10, interval_days=30)
    existing = SimpleNamespace(id=uuid.uuid4(), status=ReturnOpportunityStatus.OPEN)

    opp_repo = FakeOpportunityRepository(active_for_sale_item=existing)
    session_repo = FakeSessionRepository(
        [
            _session(
                status=SessionStatus.COMPLETED,
                completed_at=datetime(2026, 3, 1, 10, 0, 0, tzinfo=UTC),
            )
        ]
    )
    svc = RetentionService(opp_repo, session_repo)

    opportunity = svc.check_and_create_opportunity(
        sale_item=sale_item, patient_id=uuid.uuid4(), professional_timezone="UTC"
    )

    assert opportunity is None
    assert opp_repo.added == []
    # não deveria nem precisar olhar sessions, já bloqueou pelo repo
    assert session_repo.list_for_sale_item_calls == []


def test_close_open_opportunities_fecha_e_carimba_resolved_by_sale_id():
    """NOTA: usa status=BOOKED, não OPEN, porque a tabela de transições
    atual (app/domain/retention/return_opportunity_state_machine.py,
    Task 1) só permite BOOKED/DECLINED -> CLOSED. O design doc
    (docs/superpowers/specs/2026-09-01-motor-de-retencao-design.md,
    seção "Fechamento automático por venda (T-028)") descreve o
    fechamento automático como uma transição OPEN/CONTACTED -> CLOSED,
    o que hoje não está na tabela de transições da Task 1 — ver o teste
    seguinte, que documenta essa lacuna pré-existente. Este teste cobre
    o caminho que a máquina de estados atual de fato permite."""
    opportunity = SimpleNamespace(
        status=ReturnOpportunityStatus.BOOKED, resolved_by_sale_id=None
    )
    opp_repo = FakeOpportunityRepository(open_or_contacted=[opportunity])
    session_repo = FakeSessionRepository([])
    svc = RetentionService(opp_repo, session_repo)

    patient_id = uuid.uuid4()
    procedure_id = uuid.uuid4()
    new_sale_id = uuid.uuid4()

    svc.close_open_opportunities(
        patient_id=patient_id,
        procedure_id=procedure_id,
        resolved_by_sale_id=new_sale_id,
    )

    assert opportunity.status == ReturnOpportunityStatus.CLOSED
    assert opportunity.resolved_by_sale_id == new_sale_id
    assert opp_repo.list_open_or_contacted_calls == [(patient_id, procedure_id)]
    assert opp_repo.flush_calls == 1


def test_close_open_opportunities_chama_validate_transition_antes_do_update():
    """Prova que close_open_opportunities NÃO confia no chamador: delega
    100% da validação a validate_transition, sem short-circuit próprio.
    Usa DISMISSED (estado terminal) para provar isso de forma
    inequívoca — mas o mesmo mecanismo é o que hoje bloqueia
    OPEN/CONTACTED -> CLOSED (ver nota no teste anterior), que é o caso
    realista de T-028 ("Regra de fechamento", backend/BACKLOG.md linha
    186: "Fecha na venda, não na sessão"). Ou seja: com os dados reais
    que list_open_or_contacted_for_patient_and_procedure() devolve
    (status OPEN/CONTACTED/NO_RESPONSE), close_open_opportunities()
    levanta InvalidReturnOpportunityTransitionError sempre — bug
    pré-existente na máquina de estados da Task 1, fora do escopo desta
    task (ver task-5-report.md)."""
    opportunity = SimpleNamespace(
        status=ReturnOpportunityStatus.DISMISSED, resolved_by_sale_id=None
    )
    opp_repo = FakeOpportunityRepository(open_or_contacted=[opportunity])
    svc = RetentionService(opp_repo, FakeSessionRepository([]))

    with pytest.raises(InvalidReturnOpportunityTransitionError):
        svc.close_open_opportunities(
            patient_id=uuid.uuid4(),
            procedure_id=uuid.uuid4(),
            resolved_by_sale_id=uuid.uuid4(),
        )


def test_close_open_opportunities_com_status_open_real_levanta_bug_conhecido():
    """Documenta o comportamento REAL e ATUAL (não o desejado) quando
    close_open_opportunities recebe o status que
    list_open_or_contacted_for_patient_and_procedure() de fato devolve
    em produção (OPEN). Isso vai FALHAR ao "fechar" — levanta em vez de
    fechar — porque OPEN -> CLOSED não está na tabela de transições da
    Task 1, apesar do design doc de T-028 descrever exatamente esse
    caminho como o fluxo principal do fechamento automático por venda.
    Este teste existe para que qualquer correção futura da máquina de
    estados (Task 1) quebre este teste em vez de mascarar o problema —
    quando isso acontecer, atualizar para assert de sucesso."""
    opportunity = SimpleNamespace(
        status=ReturnOpportunityStatus.OPEN, resolved_by_sale_id=None
    )
    opp_repo = FakeOpportunityRepository(open_or_contacted=[opportunity])
    svc = RetentionService(opp_repo, FakeSessionRepository([]))

    with pytest.raises(InvalidReturnOpportunityTransitionError):
        svc.close_open_opportunities(
            patient_id=uuid.uuid4(),
            procedure_id=uuid.uuid4(),
            resolved_by_sale_id=uuid.uuid4(),
        )
