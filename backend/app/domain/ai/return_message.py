"""Texto de retorno para a paciente — parte pura (sem rede, sem banco).

A IA só recebe o necessário para escrever uma mensagem curta: primeiro nome,
nome do procedimento e há quantos dias venceu. Nunca telefone, CPF, valor em
R$ nem dado de saúde (REV-20).
"""

from dataclasses import dataclass

MAX_MESSAGE_CHARS = 600

SYSTEM_PROMPT = (
    "Você escreve mensagens curtas de WhatsApp, em português do Brasil, para uma "
    "esteticista chamar uma paciente de volta. Tom caloroso, pessoal e direto, "
    "no máximo 3 frases, sem emojis em excesso. Não invente preço, desconto, "
    "promoção, prazo nem promessa de resultado. Não mencione saúde, diagnóstico "
    "ou condição da paciente. Responda apenas com o texto da mensagem."
)


@dataclass(frozen=True)
class ReturnMessageContext:
    patient_first_name: str
    procedure_name: str
    days_overdue: int  # negativo = ainda não venceu


def first_name(full_name: str) -> str:
    parts = full_name.strip().split()
    return parts[0] if parts else ""


def fallback_message(ctx: ReturnMessageContext) -> str:
    """Texto fixo usado quando a IA está desligada, no teto ou fora do ar."""
    nome = ctx.patient_first_name
    saudacao = f"Oi, {nome}!" if nome else "Oi!"
    return (
        f"{saudacao} Tudo bem? Já está na época de fazer {ctx.procedure_name} de "
        "novo. Quer que eu veja um horário para você esta semana?"
    )


def build_user_prompt(ctx: ReturnMessageContext) -> str:
    if ctx.days_overdue > 0:
        quando = f"venceu há {ctx.days_overdue} dias"
    elif ctx.days_overdue == 0:
        quando = "vence hoje"
    else:
        quando = f"vence em {-ctx.days_overdue} dias"
    return (
        f"Paciente: {ctx.patient_first_name}\n"
        f"Procedimento: {ctx.procedure_name}\n"
        f"O retorno {quando}.\n"
        "Escreva a mensagem."
    )


def clean_generated(text: str | None) -> str | None:
    """Normaliza a saída do modelo; vazio ou longo demais vira None (→ fallback)."""
    if not text:
        return None
    cleaned = text.strip().strip('"').strip()
    if not cleaned or len(cleaned) > MAX_MESSAGE_CHARS:
        return None
    return cleaned
