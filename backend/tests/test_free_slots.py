"""Épico A — "Modo Ocupado" (free slots). PURO, sem I/O nem banco."""

from datetime import time

from app.domain.agenda.free_slots import Occupied, WorkWindow, compute_free_slots


def test_dia_totalmente_vazio_gera_slots_cobrindo_toda_a_janela():
    window = WorkWindow(
        start=time(8, 0), end=time(9, 0), slot_minutes=30, buffer_minutes=0
    )

    slots = compute_free_slots(occupied=[], window=window)

    assert slots == [time(8, 0), time(8, 30)]


def test_compromisso_ocupado_remove_o_slot_correspondente():
    window = WorkWindow(
        start=time(8, 0), end=time(9, 0), slot_minutes=30, buffer_minutes=0
    )

    slots = compute_free_slots(occupied=[Occupied(start=time(8, 0))], window=window)

    assert slots == [time(8, 30)]


def test_buffer_bloqueia_slots_antes_e_depois_do_compromisso():
    window = WorkWindow(
        start=time(8, 0), end=time(10, 0), slot_minutes=30, buffer_minutes=15
    )

    # Compromisso 9h-9h30 (duração = slot_minutes). Com 15min de buffer
    # de cada lado, o intervalo bloqueado é 8h45-9h45: o slot 8h30-9h00
    # (sobrepõe a partir de 8h45) e o slot 9h30-10h00 (começa dentro do
    # bloqueio, até 9h45) ficam indisponíveis. Só sobra 8h00.
    slots = compute_free_slots(occupied=[Occupied(start=time(9, 0))], window=window)

    assert slots == [time(8, 0)]


def test_varios_compromissos_bloqueiam_seus_proprios_intervalos():
    window = WorkWindow(
        start=time(8, 0), end=time(10, 0), slot_minutes=30, buffer_minutes=0
    )

    slots = compute_free_slots(
        occupied=[Occupied(start=time(8, 0)), Occupied(start=time(9, 30))],
        window=window,
    )

    assert slots == [time(8, 30), time(9, 0)]


def test_janela_menor_que_um_slot_nao_gera_nenhum_horario():
    window = WorkWindow(
        start=time(8, 0), end=time(8, 15), slot_minutes=30, buffer_minutes=0
    )

    slots = compute_free_slots(occupied=[], window=window)

    assert slots == []
