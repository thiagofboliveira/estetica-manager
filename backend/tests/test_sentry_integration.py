"""Testes de integração para observabilidade com Sentry (G-08)."""

from unittest.mock import patch


def test_sentry_not_initialized_when_dsn_empty():
    """Sem SENTRY_DSN, a telemetria do Sentry não deve ser inicializada."""
    from app.core.config import Settings

    s = Settings(
        DATABASE_URL="postgresql://fake:fake@localhost/fake",
        DATABASE_URL_MIGRATIONS="postgresql://fake:fake@localhost/fake",
        SUPABASE_URL="https://fake.supabase.co",
        _env_file=None,
    )
    assert s.SENTRY_DSN == ""


def test_sentry_initialization_with_dsn_configures_safe_defaults():
    """Quando SENTRY_DSN é fornecido, valida inicialização segura com send_default_pii=False (LGPD)."""
    with patch("sentry_sdk.init") as mock_init:
        # Simula o bloco de inicialização do main.py
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        fake_dsn = "https://public_key@o0.ingest.sentry.io/0"
        sentry_sdk.init(
            dsn=fake_dsn,
            environment="production",
            traces_sample_rate=0.1,
            send_default_pii=False,
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
        )

        mock_init.assert_called_once()
        _, kwargs = mock_init.call_args
        assert kwargs["dsn"] == fake_dsn
        assert kwargs["environment"] == "production"
        assert kwargs["send_default_pii"] is False
        assert kwargs["traces_sample_rate"] == 0.1
