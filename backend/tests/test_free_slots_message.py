"""Épico A — "Modo Ocupado": mensagem pronta para colar no WhatsApp."""

from datetime import time

from app.domain.messaging.templates import build_free_slots_message


def test_um_horario_livre():
    msg = build_free_slots_message([time(14, 0)])
    assert msg == "Oi! Tenho horário livre hoje às 14h. Qual fica melhor pra você?"


def test_varios_horarios_livres_lista_corrida():
    msg = build_free_slots_message([time(14, 0), time(15, 30), time(16, 0)])
    assert (
        msg
        == "Oi! Tenho horário livre hoje às 14h, 15h30 e 16h. Qual fica melhor pra você?"
    )
