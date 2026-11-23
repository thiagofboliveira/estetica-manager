"""AI-01 — suporte a vários provedores (Groq, Anthropic, OpenAI, compatíveis).

Sem rede: httpx.post é substituído; o banco não é usado.
"""

import httpx
import pytest

from app.core.config import settings
from app.services.ai_providers import (
    AnthropicProvider,
    ChainProvider,
    OpenAICompatibleProvider,
    build_provider,
)

NO_KEYS = {
    "AI_PROVIDER": None,
    "ANTHROPIC_API_KEY": None,
    "GROQ_API_KEY": None,
    "OPENAI_API_KEY": None,
    "AI_API_KEY": None,
    "AI_BASE_URL": None,
}


def cfg(**kw):
    return settings.model_copy(update={**NO_KEYS, **kw})


class TestBuildProvider:
    def test_sem_chave_nenhuma_desliga_a_ia(self) -> None:
        assert build_provider(cfg()) is None

    def test_so_groq_usa_groq(self) -> None:
        p = build_provider(cfg(GROQ_API_KEY="g"))
        assert isinstance(p, OpenAICompatibleProvider)

    def test_so_anthropic_usa_anthropic(self) -> None:
        assert isinstance(build_provider(cfg(ANTHROPIC_API_KEY="a")), AnthropicProvider)

    def test_varias_chaves_sem_escolha_vira_cadeia(self) -> None:
        p = build_provider(cfg(GROQ_API_KEY="g", ANTHROPIC_API_KEY="a"))
        assert isinstance(p, ChainProvider)

    def test_ai_provider_explicito_respeita_a_escolha(self) -> None:
        p = build_provider(
            cfg(AI_PROVIDER="anthropic", GROQ_API_KEY="g", ANTHROPIC_API_KEY="a")
        )
        assert isinstance(p, AnthropicProvider)

    def test_escolhido_sem_chave_e_ignorado(self) -> None:
        assert build_provider(cfg(AI_PROVIDER="groq")) is None

    def test_nome_desconhecido_e_ignorado(self) -> None:
        p = build_provider(cfg(AI_PROVIDER="xpto,groq", GROQ_API_KEY="g"))
        assert isinstance(p, OpenAICompatibleProvider)

    def test_compativel_exige_url_e_chave(self) -> None:
        assert build_provider(cfg(AI_PROVIDER="openai_compatible", AI_API_KEY="k")) is None
        p = build_provider(
            cfg(
                AI_PROVIDER="openai_compatible",
                AI_API_KEY="k",
                AI_BASE_URL="https://openrouter.ai/api/v1",
                AI_MODEL="m",
            )
        )
        assert isinstance(p, OpenAICompatibleProvider)


class TestOpenAICompatibleRequest:
    def test_groq_usa_base_url_bearer_e_formato_de_chat(self, monkeypatch) -> None:
        seen: dict = {}

        def fake_post(url, *, headers, json, timeout):
            seen.update(url=url, headers=headers, json=json, timeout=timeout)
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "Oi, Ana!"}}]},
                request=httpx.Request("POST", url),
            )

        monkeypatch.setattr(httpx, "post", fake_post)
        p = build_provider(cfg(GROQ_API_KEY="gsk_falsa", GROQ_MODEL="modelo-g"))
        assert p is not None
        assert p.complete(system="sys", user="usr", max_tokens=50) == "Oi, Ana!"
        assert seen["url"] == "https://api.groq.com/openai/v1/chat/completions"
        assert seen["headers"]["authorization"] == "Bearer gsk_falsa"
        assert seen["json"]["model"] == "modelo-g"
        assert seen["json"]["messages"] == [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "usr"},
        ]

    def test_resposta_sem_choices_devolve_none(self, monkeypatch) -> None:
        monkeypatch.setattr(
            httpx,
            "post",
            lambda url, **_: httpx.Response(
                200, json={"choices": []}, request=httpx.Request("POST", url)
            ),
        )
        p = OpenAICompatibleProvider("https://x/v1/", "k", "m", 5)
        assert p.complete(system="s", user="u", max_tokens=1) is None


class Fake:
    def __init__(self, reply=None, error=None):
        self.reply, self.error, self.calls = reply, error, 0

    def complete(self, *, system, user, max_tokens):
        self.calls += 1
        if self.error:
            raise self.error
        return self.reply


class TestChain:
    def test_usa_o_primeiro_que_responde(self) -> None:
        a, b = Fake("A"), Fake("B")
        assert ChainProvider([("a", a), ("b", b)]).complete(
            system="s", user="u", max_tokens=1
        ) == "A"
        assert b.calls == 0

    def test_limite_de_taxa_passa_para_o_proximo(self) -> None:
        limited = Fake(error=httpx.HTTPError("429 rate limit"))
        ok = Fake("B")
        out = ChainProvider([("groq", limited), ("anthropic", ok)]).complete(
            system="s", user="u", max_tokens=1
        )
        assert out == "B" and limited.calls == 1 and ok.calls == 1

    def test_resposta_vazia_tambem_passa_para_o_proximo(self) -> None:
        out = ChainProvider([("a", Fake("  ")), ("b", Fake("B"))]).complete(
            system="s", user="u", max_tokens=1
        )
        assert out == "B"

    def test_todos_falhando_levanta_para_o_servico_cair_no_texto_fixo(self) -> None:
        chain = ChainProvider(
            [("a", Fake(error=TimeoutError())), ("b", Fake(error=TimeoutError()))]
        )
        with pytest.raises(TimeoutError):
            chain.complete(system="s", user="u", max_tokens=1)
