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

from app.domain.ai import column_mapping as colmap
from app.domain.ai import loss_alert as loss
from app.domain.ai import weekly_narrative as weekly
from app.domain.ai.grounding import is_grounded
from app.domain.ai.reengagement_message import (
    ReengagementContext,
)
from app.domain.ai.reengagement_message import (
    build_user_prompt as reengagement_prompt,
)
from app.domain.ai.reengagement_message import (
    fallback_message as reengagement_fallback,
)
from app.domain.ai.return_message import (
    MAX_MESSAGE_CHARS,
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

    def _generate(
        self,
        *,
        system: str,
        user: str,
        fallback: str,
        period_month: date,
        allowed: set[str] | None = None,
        max_tokens: int = 250,
        max_chars: int = MAX_MESSAGE_CHARS,
    ) -> GeneratedText:
        """Núcleo comum: teto, provedor, limpeza, checagem de números e fallback.

        ``allowed`` ativa a checagem de números: se o texto gerado trouxer um
        número que não veio do payload, é descartado (a IA não inventa valor)."""
        used = self._usage.count_for(period_month)
        remaining = max(self._limit - used, 0)

        def fall(reason: FallbackReason, left: int) -> GeneratedText:
            self._usage.increment(period_month, "fallbacks_count")
            return GeneratedText(fallback, "fallback", reason, left)

        if self._provider is None:
            return GeneratedText(fallback, "fallback", "no_provider", remaining)
        if remaining <= 0:
            return fall("limit_reached", 0)

        try:
            raw = self._provider.complete(
                system=system, user=user, max_tokens=max_tokens
            )
        except Exception:
            logger.warning("falha no provedor de IA; usando texto fixo", exc_info=True)
            return fall("provider_error", remaining)

        text = clean_generated(raw, max_chars=max_chars)
        if text is None:
            return fall("provider_error", remaining)
        if allowed is not None and not is_grounded(text, allowed):
            logger.warning("texto da IA com número fora do payload; usando texto fixo")
            return fall("provider_error", remaining)

        used = self._usage.increment(period_month)
        return GeneratedText(text, "ai", None, max(self._limit - used, 0))

    def draft_return_message(
        self, ctx: ReturnMessageContext, *, period_month: date
    ) -> GeneratedText:
        return self._generate(
            system=SYSTEM_PROMPT,
            user=build_user_prompt(ctx),
            fallback=fallback_message(ctx),
            period_month=period_month,
            allowed=set(),  # mensagem de retorno não deve conter número algum
        )

    def draft_reengagement_message(
        self, ctx: ReengagementContext, *, period_month: date
    ) -> GeneratedText:
        return self._generate(
            system=SYSTEM_PROMPT,
            user=reengagement_prompt(ctx),
            fallback=reengagement_fallback(ctx),
            period_month=period_month,
            allowed=set(),
        )

    def narrate_weekly(
        self, ctx: weekly.WeeklyNarrativeContext, *, period_month: date
    ) -> GeneratedText:
        """AI-03: texto curto sobre o resumo da semana. Número fora do payload
        faz o texto ser descartado (a IA não inventa valor)."""
        return self._generate(
            system=weekly.SYSTEM_PROMPT,
            user=weekly.build_user_prompt(ctx),
            fallback=weekly.fallback_text(ctx),
            period_month=period_month,
            allowed=weekly.allowed_for(ctx),
            max_tokens=400,
            max_chars=weekly.MAX_NARRATIVE_CHARS,
        )

    def explain_loss_alerts(
        self, alerts: list[loss.LossAlert], *, period_month: date
    ) -> GeneratedText:
        """AI-04: explica em texto os alertas que a regra do backend escolheu.
        Número fora do payload faz o texto ser descartado."""
        return self._generate(
            system=loss.SYSTEM_PROMPT,
            user=loss.build_user_prompt(alerts),
            fallback=loss.fallback_text(alerts),
            period_month=period_month,
            allowed=loss.allowed_for(alerts),
            max_tokens=400,
            max_chars=loss.MAX_EXPLANATION_CHARS,
        )

    def map_columns(
        self, *, headers: list[str], sample_rows: list[list[str]], period_month: date
    ) -> tuple[dict[str, int | None], Source]:
        """AI-08: cabeçalho primeiro (grátis e determinístico); a IA só entra se
        faltar nome ou telefone, e só preenche o que faltou. Resposta inválida da
        IA é ignorada."""
        mapping = colmap.heuristic_mapping(headers)
        if colmap.is_confident(mapping):
            return mapping, "fallback"
        result = self._generate(
            system=colmap.SYSTEM_PROMPT,
            user=colmap.build_user_prompt(headers, sample_rows),
            fallback="",
            period_month=period_month,
            max_tokens=200,
            max_chars=400,
        )
        if result.source != "ai":
            return mapping, "fallback"
        parsed = colmap.parse_ai_mapping(result.text, len(headers))
        if parsed is None:
            return mapping, "fallback"
        return colmap.merge(mapping, parsed), "ai"

    def record_feedback(self, *, period_month: date, edited: bool) -> None:
        """AI-05: a profissional enviou um rascunho da IA (editado ou não)."""
        self._usage.increment(period_month, "sent_count")
        if edited:
            self._usage.increment(period_month, "edited_count")

    def usage(self, period_month: date) -> dict[str, int]:
        row = self._usage.get_month(period_month)
        generated = row.drafts_count if row else 0
        return {
            "limit": self._limit,
            "generated": generated,
            "remaining": max(self._limit - generated, 0),
            "fallbacks": row.fallbacks_count if row else 0,
            "sent": row.sent_count if row else 0,
            "sent_edited": row.edited_count if row else 0,
        }
