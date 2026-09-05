"""S-04 — rate limit por IP em POST /system/setup.

Ver docs/pending/BACKLOG_GO_LIVE.md S-04. Diferente do rate limit de
POST /patients/import (por professional_id, rota autenticada), esta
rota é pública — alcançada antes de qualquer JWT — então a chave
disponível é o IP do cliente, não um tenant.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

pytestmark = pytest.mark.skipif(
    not settings.DEV_AUTH_SECRET, reason="requer DEV_AUTH_SECRET + Postgres real"
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_setup_bloqueia_apos_5_chamadas_por_ip(client: TestClient) -> None:
    # As primeiras 5 podem falhar por outro motivo (sistema já
    # inicializado neste banco de dev compartilhado) — o que importa é
    # que a 6ª chamada do MESMO IP seja 429, não o status das anteriores.
    for _ in range(5):
        client.post(
            "/api/v1/system/setup",
            json={
                "clinic_name": "Rate Limit Test",
                "admin_name": "Teste",
                "email": "rate-limit-test@example.com",
            },
        )

    resp = client.post(
        "/api/v1/system/setup",
        json={
            "clinic_name": "Rate Limit Test",
            "admin_name": "Teste",
            "email": "rate-limit-test-2@example.com",
        },
    )
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers
