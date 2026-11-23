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
from typing import Literal, Protocol

import httpx

from app.domain.ai.return_message import (
    SYSTEM_PROMPT,
    ReturnMessageContext,
    build_user_prompt,
    clean_generated,
    fallback_message,
)
from app.repositories.ai_usage import AIUsageRepository

logger = logging.getLogger(__name__)

Source = Literal["ai", "fallback"]
FallbackReason = Literal["no_provider", "limit_reached", "provider_error"]


class TextProvider(Protocol):
    def complete(self, *, system: str, user: str, max_tokens: int) -> str | None: ...


class AnthropicProvider:
    """Provedor real, via API de mensagens da Anthropic."""

    URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str, model: str, timeout: float) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    def complete(self, *, system: str, user: str, max_tokens: int) -> str | None:
        resp = httpx.post(
            self.URL,
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self._model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
            timeout=self._timeout,
        )
        resp.raise_for_status()
        blocks = resp.json().get("content") or []
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")


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
