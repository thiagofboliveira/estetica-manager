"""core/tz.py — invariante I4 (MVP v6 §3): trunca no fuso da
profissional, nunca em UTC."""

from datetime import UTC, date, datetime

from app.core.tz import utc_to_local_date


def test_22h_sao_paulo_nao_vira_dia_seguinte_em_utc() -> None:
    # 2026-03-12 22:00 America/Sao_Paulo (UTC-3) = 2026-03-13 01:00 UTC.
    # Sem a conversão, truncar em UTC daria 13/03 — errado, ela vendeu
    # no dia 12.
    moment_utc = datetime(2026, 3, 13, 1, 0, tzinfo=UTC)
    assert utc_to_local_date(moment_utc, "America/Sao_Paulo") == date(2026, 3, 12)


def test_horario_naive_e_tratado_como_utc() -> None:
    moment_naive = datetime(2026, 3, 13, 1, 0)
    assert utc_to_local_date(moment_naive, "America/Sao_Paulo") == date(2026, 3, 12)


def test_fuso_sem_deslocamento_bate_direto() -> None:
    moment_utc = datetime(2026, 3, 12, 23, 0, tzinfo=UTC)
    assert utc_to_local_date(moment_utc, "UTC") == date(2026, 3, 12)
