"""G-06 — /health precisa checar o banco, não só responder "ok" de
memória.

Ver docs/pending/BACKLOG_GO_LIVE.md G-06. Antes desta correção, o
endpoint respondia 200 mesmo com o Postgres caído — o Railway
(healthcheckPath em railway.json) nunca detectaria a falha real nem
reiniciaria o container.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def test_health_ok_com_banco_disponivel() -> None:
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_503_com_banco_indisponivel() -> None:
    client = TestClient(app)
    with patch(
        "app.main.unsafe_session_without_tenant",
        side_effect=Exception("conexão recusada"),
    ):
        resp = client.get("/health")
    assert resp.status_code == 503
