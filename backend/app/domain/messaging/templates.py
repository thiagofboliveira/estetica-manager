"""Templates de Mensagens para Canais Externos (WhatsApp) (EPIC-S2-02, TASK-BACK-S2-08)."""

from urllib.parse import quote


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
