"""Catálogo fechado de nomes de evento de ativação (G-13).

StrEnum, não string solta: um nome de evento espalhado como literal
pelo código é impossível de auditar depois ("quais eventos existem
mesmo?" vira grep manual). Puro — sem sqlalchemy nem fastapi (mesma
regra de app/domain/, test_dominio_nao_importa_infraestrutura).
"""

from enum import StrEnum


class EventName(StrEnum):
    SIGNED_UP = "signed_up"
    FIRST_LOGIN = "first_login"
    FIRST_PROCEDURE_CREATED = "first_procedure_created"
    FIRST_PATIENT_IMPORTED = "first_patient_imported"
    FIRST_SALE_RECORDED = "first_sale_recorded"
    FIRST_PROFIT_VIEWED = "first_profit_viewed"
    FIRST_REACTIVATION_SENT = "first_reactivation_sent"
    FIRST_REACTIVATION_CONVERTED = "first_reactivation_converted"
    FIRST_PUBLIC_BOOKING_RECEIVED = "first_public_booking_received"
    PUBLIC_BOOKING_CREATED = "public_booking_created"

