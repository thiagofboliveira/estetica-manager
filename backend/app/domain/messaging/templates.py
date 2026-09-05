"""Templates de Mensagens para Canais Externos (WhatsApp) (EPIC-S2-02, TASK-BACK-S2-08)."""

from datetime import time
from urllib.parse import quote


def _format_time(t: time) -> str:
    return f"{t.hour}h" if t.minute == 0 else f"{t.hour}h{t.minute:02d}"


def build_confirmation_message(
    patient_name: str,
    procedure_name: str,
    scheduled_time: str,
) -> str:
    """Monta a mensagem de confirmação de agendamento D-1."""
    first_name = patient_name.strip().split()[0] if patient_name else ""
    return (
        f"Oi {first_name}! 😊 Lembrete da sua sessão de {procedure_name} amanhã às {scheduled_time}. "
        f"Posso confirmar? 💜"
    )


def build_free_slots_message(slots: list[time]) -> str:
    """Épico A — "Modo Ocupado": texto pronto pra colar no WhatsApp com
    os horários livres do dia, em lista corrida ("14h, 15h30 e 16h")."""
    formatted = [_format_time(s) for s in slots]
    if len(formatted) == 1:
        joined = formatted[0]
    else:
        joined = ", ".join(formatted[:-1]) + f" e {formatted[-1]}"
    return f"Oi! Tenho horário livre hoje às {joined}. Qual fica melhor pra você?"


def build_whatsapp_link(phone: str | None, message: str) -> str | None:
    """Gera link wa.me pronto para abertura no navegador/app."""
    if not phone:
        return None
    clean_digits = "".join(filter(str.isdigit, phone))
    if not clean_digits:
        return None
    # Adiciona DDI 55 caso venha com 10 ou 11 dígitos
    if len(clean_digits) in (10, 11):
        clean_digits = f"55{clean_digits}"
    encoded = quote(message)
    return f"https://wa.me/{clean_digits}?text={encoded}"
