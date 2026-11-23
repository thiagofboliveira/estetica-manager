"""Base hermética para os testes de integração (REV-08).

Vários testes assumem que existe um usuário administrador "dev" (o
`/dev/login` pega o usuário mais antigo) e o professional fixo
`00000000-0000-0000-0000-000000000001`. Antes isso só existia por efeito
colateral de testes anteriores ou de um banco de desenvolvimento já usado:
num banco novo (CI limpo, outra máquina) 15 testes falhavam.

Esta fixture cria essa base uma vez por sessão, de forma idempotente, e a
faz ser o usuário MAIS ANTIGO (created_at fixo no passado) para que
`/dev/login` sempre resolva para ela.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from app.core.config import settings

BASELINE_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
BASELINE_CLINIC_ID = uuid.UUID("00000000-0000-0000-0000-0000000000c1")
_OLD = datetime(2000, 1, 1, tzinfo=UTC)


@pytest.fixture(scope="session", autouse=True)
def baseline_dev_tenant() -> None:
    if settings.ENV != "development" or not settings.DEV_AUTH_SECRET:
        return

    from sqlalchemy.exc import OperationalError

    from app.db.session import unsafe_session_without_tenant
    from app.models.clinic import Clinic
    from app.models.professional import Professional
    from app.models.user import User

    try:
        with unsafe_session_without_tenant("seed baseline dev tenant") as session:
            if session.get(User, BASELINE_ID) is not None:
                return
            session.add(
                Clinic(id=BASELINE_CLINIC_ID, name="Clínica Base de Testes", created_at=_OLD)
            )
            session.flush()
            session.add(
                User(
                    id=BASELINE_ID,
                    clinic_id=BASELINE_CLINIC_ID,
                    name="Admin Base de Testes",
                    email="base-testes@example.com",
                    role="superadmin",
                    is_superuser=True,
                    is_active=True,
                    created_at=_OLD,
                )
            )
            session.flush()
            session.add(
                Professional(
                    id=BASELINE_ID,
                    user_id=BASELINE_ID,
                    clinic_id=BASELINE_CLINIC_ID,
                    name="Admin Base de Testes",
                    slug="base-testes-0001",
                    timezone="America/Sao_Paulo",
                    is_active=True,
                )
            )
            session.commit()
    except OperationalError:
        # Sem banco: os testes de integração se auto-ignoram/falham por si.
        return
