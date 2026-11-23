"""Provedores de IA de texto (AI-01).

Três jeitos de falar com um provedor, escolhidos por configuração:
- ``anthropic``: API de mensagens da Anthropic;
- ``groq`` / ``openai``: API no formato OpenAI (``/chat/completions``);
- ``openai_compatible``: qualquer outro endereço nesse formato (OpenRouter,
  Together, um servidor próprio...), com ``AI_BASE_URL`` e ``AI_API_KEY``.

``AI_PROVIDER`` aceita uma lista separada por vírgula (``groq,anthropic``): a
cadeia tenta na ordem e passa para o próximo quando um falha (limite de taxa
do free tier, timeout, erro). Se nenhum responder, o serviço usa o texto fixo.
"""

import logging
from typing import Protocol

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
OPENAI_BASE_URL = "https://api.openai.com/v1"

KNOWN_PROVIDERS = ("anthropic", "groq", "openai", "openai_compatible")


class TextProvider(Protocol):
    def complete(self, *, system: str, user: str, max_tokens: int) -> str | None: ...


class AnthropicProvider:
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


class OpenAICompatibleProvider:
    """Formato ``/chat/completions``: Groq, OpenAI e similares."""

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float) -> None:
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    def complete(self, *, system: str, user: str, max_tokens: int) -> str | None:
        resp = httpx.post(
            self._url,
            headers={
                "authorization": f"Bearer {self._api_key}",
                "content-type": "application/json",
            },
            json={
                "model": self._model,
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=self._timeout,
        )
        resp.raise_for_status()
        choices = resp.json().get("choices") or []
        if not choices:
            return None
        return (choices[0].get("message") or {}).get("content")


class ChainProvider:
    """Tenta cada provedor na ordem; devolve o primeiro texto não vazio."""

    def __init__(self, providers: list[tuple[str, TextProvider]]) -> None:
        self._providers = providers

    def complete(self, *, system: str, user: str, max_tokens: int) -> str | None:
        last_error: Exception | None = None
        for name, provider in self._providers:
            try:
                text = provider.complete(
                    system=system, user=user, max_tokens=max_tokens
                )
            except Exception as exc:
                logger.warning("provedor de IA %r falhou; tentando o próximo", name)
                last_error = exc
                continue
            if text and text.strip():
                return text
        if last_error is not None:
            raise last_error
        return None


def _requested_names(cfg: Settings) -> list[str]:
    raw = (cfg.AI_PROVIDER or "").strip().lower()
    if raw:
        return [n.strip() for n in raw.split(",") if n.strip()]
    # Sem escolha explícita: usa o que tiver chave, nesta ordem.
    auto = []
    if cfg.GROQ_API_KEY:
        auto.append("groq")
    if cfg.ANTHROPIC_API_KEY:
        auto.append("anthropic")
    if cfg.OPENAI_API_KEY:
        auto.append("openai")
    if cfg.AI_API_KEY and cfg.AI_BASE_URL:
        auto.append("openai_compatible")
    return auto


def _build_one(name: str, cfg: Settings) -> TextProvider | None:
    t = cfg.AI_TIMEOUT_SECONDS
    if name == "anthropic" and cfg.ANTHROPIC_API_KEY:
        return AnthropicProvider(cfg.ANTHROPIC_API_KEY, cfg.ANTHROPIC_MODEL, t)
    if name == "groq" and cfg.GROQ_API_KEY:
        return OpenAICompatibleProvider(
            GROQ_BASE_URL, cfg.GROQ_API_KEY, cfg.GROQ_MODEL, t
        )
    if name == "openai" and cfg.OPENAI_API_KEY:
        return OpenAICompatibleProvider(
            OPENAI_BASE_URL, cfg.OPENAI_API_KEY, cfg.OPENAI_MODEL, t
        )
    if name == "openai_compatible" and cfg.AI_API_KEY and cfg.AI_BASE_URL:
        return OpenAICompatibleProvider(
            cfg.AI_BASE_URL, cfg.AI_API_KEY, cfg.AI_MODEL, t
        )
    if name not in KNOWN_PROVIDERS:
        logger.warning("AI_PROVIDER com nome desconhecido ignorado: %r", name)
    return None


def build_provider(cfg: Settings) -> TextProvider | None:
    """Monta o provedor a partir da configuração; None = IA desligada (texto fixo)."""
    built = []
    for name in _requested_names(cfg):
        provider = _build_one(name, cfg)
        if provider is not None:
            built.append((name, provider))
    if not built:
        return None
    return built[0][1] if len(built) == 1 else ChainProvider(built)
