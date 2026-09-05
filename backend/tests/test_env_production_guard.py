"""S-01d — o guard de ENV=production tem de ser provado, não confiado.

Ver docs/pending/BACKLOG_GO_LIVE.md §3. Estes testes existem porque a
auditoria de 2026-09-04 encontrou um fail-open: `ENV` tinha default
"development", o `DEV_AUTH_SECRET` tinha fallback hardcoded, e nem o
Dockerfile nem o railway.json definiam `ENV`. Variável esquecida no
painel de deploy abriria /dev/login público, devolvendo token de
superadmin por 24h sem senha.

Nenhum dos 42 arquivos de teste cobria esse caminho — foi exatamente por
isso que o defeito sobreviveu à construção inteira do MVP. A regra que
ficou (Definition of Done): quem toca autenticação ou o guard de ENV
prova o comportamento em produção com teste.
"""

import importlib

import pytest
from fastapi.testclient import TestClient


def _reload_app_with_env(monkeypatch: pytest.MonkeyPatch, **env: str):
    """Recarrega app.main com o ambiente dado.

    O guard de `/dev/*` é avaliado no import de app.main (`if
    settings.ENV == "development"`), e `get_settings` é cacheado com
    lru_cache — então trocar a variável exige limpar o cache e reimportar
    a cadeia inteira de módulos que capturam `settings` no import.
    """
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    import app.core.config

    app.core.config.get_settings.cache_clear()
    importlib.reload(app.core.config)

    import app.core.security

    importlib.reload(app.core.security)

    import app.main

    return importlib.reload(app.main)


@pytest.fixture(autouse=True)
def _restore_modules():
    """Devolve os módulos ao estado de dev — senão os testes seguintes
    (que dependem de /dev/login) herdam um app em modo produção."""
    yield
    import app.core.config

    app.core.config.get_settings.cache_clear()
    importlib.reload(app.core.config)
    import app.core.security

    importlib.reload(app.core.security)
    import app.main

    importlib.reload(app.main)


class TestEnvDefaultNegaAcesso:
    def test_env_default_e_production_nao_development(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """S-01a: configuração ausente tem de NEGAR, não conceder.

        Simula o cenário real de produção: sem arquivo .env (o deploy não
        tem um) e sem a variável ENV no ambiente. `env_file=None` desliga
        a leitura do .env local, que em dev define ENV=development.
        """
        monkeypatch.delenv("ENV", raising=False)

        from app.core.config import Settings

        settings = Settings(
            _env_file=None,
            DATABASE_URL="postgresql://x/y",
            DATABASE_URL_MIGRATIONS="postgresql://x/y",
            SUPABASE_URL="https://x.supabase.co",
        )
        assert settings.ENV == "production", (
            "ENV default deve ser 'production' — default permissivo é uma "
            "falha de segurança esperando por um deploy distraído"
        )


class TestDevRoutesMorremEmProducao:
    def test_dev_login_nao_existe_com_env_production(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """O endpoint que devolve token de superadmin sem senha não pode
        sequer estar registrado fora de development."""
        main = _reload_app_with_env(
            monkeypatch, ENV="production", DEV_AUTH_SECRET="irrelevante-em-producao"
        )
        client = TestClient(main.app)

        resp = client.post("/dev/login")
        assert resp.status_code == 404, (
            f"/dev/login respondeu {resp.status_code} em ENV=production — "
            "deveria não existir (404)"
        )

    def test_dev_impersonate_nao_existe_com_env_production(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        main = _reload_app_with_env(
            monkeypatch, ENV="production", DEV_AUTH_SECRET="irrelevante-em-producao"
        )
        client = TestClient(main.app)

        resp = client.post(
            "/dev/impersonate", json={"user_id": "00000000-0000-0000-0000-000000000001"}
        )
        assert resp.status_code == 404, (
            f"/dev/impersonate respondeu {resp.status_code} em ENV=production"
        )

    def test_nenhuma_rota_dev_registrada_em_producao(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Varre o router inteiro: nenhum path /dev/* deve existir.

        Mais forte que testar os dois endpoints conhecidos — pega também
        um /dev/* novo que alguém adicione no futuro sem o guard.
        """
        main = _reload_app_with_env(
            monkeypatch, ENV="production", DEV_AUTH_SECRET="irrelevante-em-producao"
        )

        dev_routes = [
            r.path for r in main.app.routes if getattr(r, "path", "").startswith("/dev")
        ]
        assert dev_routes == [], f"rotas /dev/* registradas em produção: {dev_routes}"

    def test_health_continua_publico_em_producao(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Contraprova: o guard não pode derrubar o healthcheck junto —
        o Railway depende dele (railway.json:9)."""
        main = _reload_app_with_env(
            monkeypatch, ENV="production", DEV_AUTH_SECRET="irrelevante"
        )
        client = TestClient(main.app)

        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestSegredoSemFallback:
    def test_decode_dev_sem_secret_nao_usa_fallback_hardcoded(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """S-01b: sem DEV_AUTH_SECRET, `_decode_dev` tem de recusar.

        O fallback anterior ("dev-secret-estetica-local-key-superadmin-
        2026") assinava token de superadmin — um segredo com default é um
        segredo público, e este estava committado em dois arquivos.
        """
        from fastapi import HTTPException

        import app.core.security as security

        monkeypatch.setattr(security.settings, "DEV_AUTH_SECRET", None)

        with pytest.raises(HTTPException) as exc:
            security._decode_dev("qualquer.token.aqui")

        assert exc.value.status_code == 500
        assert "DEV_AUTH_SECRET" in exc.value.detail

    def test_fallback_hardcoded_nao_existe_mais_no_codigo(self) -> None:
        """Prova textual: o segredo committado foi removido dos dois
        arquivos onde estava (main.py e core/security.py)."""
        from pathlib import Path

        app_dir = Path(__file__).resolve().parent.parent / "app"
        ofensores = [
            str(p.relative_to(app_dir))
            for p in app_dir.rglob("*.py")
            if "dev-secret-estetica-local-key" in p.read_text(encoding="utf-8")
        ]
        assert ofensores == [], (
            f"segredo hardcoded ainda presente em: {ofensores}"
        )
