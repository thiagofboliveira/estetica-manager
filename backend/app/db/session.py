"""Sessão de banco com contexto de tenant via SET LOCAL.

Ver ../../ENGENHARIA.md invariante I2 e backend/ENGENHARIA.md §1.

O bug mais perigoso deste módulo: `SET` sem `LOCAL` persiste na CONEXÃO,
não na transação. Com pool, a conexão volta com a variável setada e o
próximo request de OUTRO tenant a herda — vazamento intermitente que só
aparece sob concorrência em produção, nunca em teste de tenant único.

set_config(name, value, is_local=true) é o equivalente parametrizável de
SET LOCAL (que não aceita bind params — só literal interpolado, o que
seria um padrão ruim mesmo com UUID validado).
"""

from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,  # role de aplicação, NÃO owner/service_role
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={"client_encoding": "utf8", "options": "-c client_encoding=utf8"},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


@event.listens_for(engine, "checkin")
def _reset_tenant_on_checkin(dbapi_conn, connection_record) -> None:
    """Cinto de segurança: SET LOCAL já reverte no commit/rollback, mas
    se algum código usar SET puro por engano, isto limpa antes da
    conexão voltar ao pool. Custo desprezível, elimina uma classe de bug.
    """
    try:
        with dbapi_conn.cursor() as cur:
            cur.execute("RESET app.professional_id")
            cur.execute("RESET app.clinic_id")
            cur.execute("RESET app.bypass_tenant")
        dbapi_conn.commit()
    except Exception:
        pass  # conexão já morta: o pool a descarta de qualquer forma


def _set_tenant(session: Session, professional_id: UUID) -> None:
    session.execute(
        text("SELECT set_config('app.professional_id', :pid, true)"),
        {"pid": str(professional_id)},
    )
    # S-02a: busca o clinic_id do Professional logado para isolamento de plataforma
    clinic_id = session.execute(
        text("SELECT clinic_id FROM professionals WHERE id = :pid"),
        {"pid": str(professional_id)},
    ).scalar()
    if clinic_id is not None:
        session.execute(
            text("SELECT set_config('app.clinic_id', :cid, true)"),
            {"cid": str(clinic_id)},
        )


def get_tenant_session(professional_id: UUID) -> Iterator[Session]:
    """Sessão com tenant fixado, em transação explícita única por request.

    session.begin() abre a transação ANTES do set_config (senão SET
    LOCAL vira no-op silencioso). O yield mantém a transação aberta
    durante todo o handler do FastAPI; commit no fim, rollback em
    qualquer exceção.
    """
    session = SessionLocal()
    try:
        with session.begin():
            _set_tenant(session, professional_id)
            yield session
    finally:
        session.close()


@contextmanager
def tenant_session(professional_id: UUID) -> Iterator[Session]:
    """Context manager com tenant fixado para operações fora da injeção do FastAPI."""
    yield from get_tenant_session(professional_id)


@contextmanager
def unsafe_session_without_tenant(reason: str) -> Iterator[Session]:
    """⚠️ Sessão SEM contexto de tenant. Utilizada para jobs de manutenção,
    setup inicial do sistema (/system/setup) ou gestão multi-clínica do Super Admin.

    Seta app.bypass_tenant localmente para permitir visão de plataforma nas tabelas
    users/clinics/professionals. As tabelas de negócio (patients, procedures, etc.)
    continuam exigindo app.professional_id explícito.

    `reason` é obrigatório de propósito: força quem chama a justificar,
    e torna trivial auditar via grep por "unsafe_session_without_tenant".
    """
    if not reason:
        raise ValueError("reason é obrigatório")
    session = SessionLocal()
    try:
        session.execute(text("SELECT set_config('app.bypass_tenant', 'true', true)"))
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
