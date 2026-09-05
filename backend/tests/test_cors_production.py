"""B-04 — CORS de produção: sem ALLOWED_ORIGINS configurado, o app não
deve conceder acesso a nenhuma origem (nunca "*"). Com a variável
setada, apenas os domínios listados são liberados.

Ver docs/pending/BACKLOG_GO_LIVE.md B-04. Antes desta correção, o
CORSMiddleware só era registrado com ENV=development (origem fixa
localhost:5173) — em produção, front e back em domínios diferentes
teriam toda chamada bloqueada pelo browser, silenciosamente (o backend
responde 200, o browser descarta a resposta).
"""

import importlib

import pytest
from fastapi.testclient import TestClient


def _reload_app_with_env(monkeypatch: pytest.MonkeyPatch, **env: str):
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    import app.core.config

    app.core.config.get_settings.cache_clear()
    importlib.reload(app.core.config)
    import app.main

    return importlib.reload(app.main)


@pytest.fixture(autouse=True)
def _restore_modules():
    yield
    import app.core.config

    app.core.config.get_settings.cache_clear()
    importlib.reload(app.core.config)
    import app.main

    importlib.reload(app.main)


class TestCorsProducao:
    def test_sem_allowed_origins_nao_libera_nenhuma_origem(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Configuração incompleta não deve virar CORS aberto — o
        cliente só descobre que falta configurar quando o browser
        bloqueia, o que é o comportamento correto (fail-closed)."""
        monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
        main = _reload_app_with_env(
            monkeypatch, ENV="production", DEV_AUTH_SECRET="irrelevante"
        )
        client = TestClient(main.app)

        resp = client.get(
            "/health",
            headers={
                "Origin": "https://qualquer-site.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" not in resp.headers

    def test_com_allowed_origins_libera_apenas_os_dominios_listados(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        main = _reload_app_with_env(
            monkeypatch,
            ENV="production",
            DEV_AUTH_SECRET="irrelevante",
            ALLOWED_ORIGINS="https://app.lumina.com.br,https://lumina-web.vercel.app",
        )
        client = TestClient(main.app)

        resp_ok = client.options(
            "/health",
            headers={
                "Origin": "https://app.lumina.com.br",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert (
            resp_ok.headers.get("access-control-allow-origin")
            == "https://app.lumina.com.br"
        )

        resp_blocked = client.options(
            "/health",
            headers={
                "Origin": "https://site-nao-autorizado.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" not in resp_blocked.headers

    def test_nunca_libera_wildcard(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Nem em produção nem em dev o allow_origins pode ser "*" —
        allow_credentials=True junto com "*" é a combinação clássica que
        navegadores recusam de qualquer forma, mas o objetivo aqui é
        nunca sequer configurar dessa forma."""
        main = _reload_app_with_env(
            monkeypatch,
            ENV="production",
            DEV_AUTH_SECRET="irrelevante",
            ALLOWED_ORIGINS="https://app.lumina.com.br",
        )
        cors_middlewares = [
            m for m in main.app.user_middleware if m.cls.__name__ == "CORSMiddleware"
        ]
        assert len(cors_middlewares) == 1
        assert cors_middlewares[0].kwargs.get("allow_origins") != ["*"]
