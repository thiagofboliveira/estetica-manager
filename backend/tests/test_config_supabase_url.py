"""REV-13: o ref do projeto Supabase vem da URL, não fixo no código."""

import pytest

from app.core.config import Settings


def _norm(url: str) -> str:
    return Settings._normalize_db_url(url)  # type: ignore[attr-defined]


def test_host_direct_vira_pooler_com_ref_da_propria_url() -> None:
    out = _norm("postgresql://postgres:segredo@db.abcdefghij.supabase.co:5432/postgres")
    assert "pooler.supabase.com" in out
    assert "postgres.abcdefghij:" in out
    assert "db.abcdefghij.supabase.co" not in out


def test_pooler_host_configuravel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPABASE_POOLER_HOST", "aws-0-sa-east-1.pooler.supabase.com")
    out = _norm("postgresql://postgres:x@db.abcdefghij.supabase.co:5432/postgres")
    assert "aws-0-sa-east-1.pooler.supabase.com" in out


def test_pooler_com_usuario_simples_usa_ref_do_supabase_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://zzzzyyyy.supabase.co")
    out = _norm("postgresql://postgres:x@aws-0-us-east-2.pooler.supabase.com:6543/postgres")
    assert "postgres.zzzzyyyy:" in out


def test_url_local_nao_muda() -> None:
    url = "postgresql+psycopg2://estetica_app:app@localhost:5434/estetica"
    assert _norm(url) == url


def test_nenhum_ref_de_projeto_fixo_no_codigo() -> None:
    import pathlib

    src = pathlib.Path(__file__).resolve().parents[1] / "app" / "core" / "config.py"
    assert "ckgnnvxnftaqtnkmovox" not in src.read_text()
