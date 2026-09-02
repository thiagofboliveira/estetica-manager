from datetime import date

from app.domain.retention.window import Timing, calculate_due_date, classify_timing


def test_calculate_due_date_soma_intervalo_em_dias():
    assert calculate_due_date(date(2026, 3, 1), 180) == date(2026, 8, 28)


def test_calculate_due_date_intervalo_zero():
    assert calculate_due_date(date(2026, 3, 1), 0) == date(2026, 3, 1)


def test_classify_timing_upcoming_quando_falta_mais_de_7_dias():
    assert classify_timing(date(2026, 9, 20), today=date(2026, 9, 1)) == Timing.UPCOMING


def test_classify_timing_due_na_borda_superior_7_dias():
    assert classify_timing(date(2026, 9, 8), today=date(2026, 9, 1)) == Timing.DUE


def test_classify_timing_due_na_borda_inferior_menos_7_dias():
    assert classify_timing(date(2026, 8, 25), today=date(2026, 9, 1)) == Timing.DUE


def test_classify_timing_due_no_dia_exato():
    assert classify_timing(date(2026, 9, 1), today=date(2026, 9, 1)) == Timing.DUE


def test_classify_timing_overdue_quando_passou_de_7_dias():
    assert classify_timing(date(2026, 8, 24), today=date(2026, 9, 1)) == Timing.OVERDUE
