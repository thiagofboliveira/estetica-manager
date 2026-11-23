"""AI-01 — camada de texto gerado por IA.

Regras que esta camada garante:
- A IA só escreve texto sobre dados já calculados; nunca calcula dinheiro.
- Provedor injetável: os testes usam um provedor falso, sem rede.
- Qualquer falha (sem chave, timeout, erro, resposta vazia, teto do mês) cai
  no texto fixo. A tela nunca quebra por causa do provedor.
- O teto mensal protege a margem: depois dele, só texto fixo.
"""

import logging
from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.domain.ai.return_message import (
    SYSTEM_PROMPT,
    ReturnMessageContext,
    build_user_prompt,
    clean_generated,
    fallback_message,
)
from app.repositories.ai_usage import AIUsageRepository
from app.services.ai_providers import AnthropicProvider, TextProvider

logger = logging.getLogger(__name__)

__all__ = ["AITextService", "AnthropicProvider", "GeneratedText", "TextProvider"]

Source = Literal["ai", "fallback"]
FallbackReason = Literal["no_provider", "limit_reached", "provider_error"]


@dataclass(frozen=True)
class GeneratedText:
    text: str
    source: Source
    reason: FallbackReason | None
    remaining: int


class AITextService:
    def __init__(
        self,
        usage_repo: AIUsageRepository,
        provider: TextProvider | None,
        monthly_limit: int,
    ) -> None:
        self._usage = usage_repo
        self._provider = provider
        self._limit = monthly_limit

    def draft_return_message(
        self, ctx: ReturnMessageContext, *, period_month: date
    ) -> GeneratedText:
        used = self._usage.count_for(period_month)
        remaining = max(self._limit - used, 0)
        fallback = fallback_message(ctx)

        if self._provider is None:
            return GeneratedText(fallback, "fallback", "no_provider", remaining)
        if remaining <= 0:
            return GeneratedText(fallback, "fallback", "limit_reached", 0)

        try:
            raw = self._provider.complete(
                system=SYSTEM_PROMPT, user=build_user_prompt(ctx), max_tokens=250
            )
        except Exception:
            logger.warning("falha no provedor de IA; usando texto fixo", exc_info=True)
            return GeneratedText(fallback, "fallback", "provider_error", remaining)

        text = clean_generated(raw)
        if text is None:
            return GeneratedText(fallback, "fallback", "provider_error", remaining)

        used = self._usage.increment(period_month)
        return GeneratedText(text, "ai", None, max(self._limit - used, 0))
