# ruff: noqa: F811
"""AI-03 — resumo semanal narrado com checagem de números."""

from datetime import date
from decimal import Decimal

from app.domain.ai.grounding import is_grounded
from app.domain.ai.weekly_narrative import (
    WeeklyNarrativeContext,
    allowed_for,
    build_user_prompt,
    fallback_text,
)
from tests.test_ai_draft_message import (  # noqa: F401
    auth_headers,
    client,
    professional_id,
    provider,
)

CTX = WeeklyNarrativeContext(
    period_start=date(2026, 11, 16),
    period_end=date(2026, 11, 22),
    gross_revenue=Decimal("1234.50"),
    net_profit=Decimal("800.00"),
    sales_count=7,
    pending_opportunities_count=3,
)


class TestDomain:
    def test_prompt_traz_os_numeros_em_formato_brasileiro(self) -> None:
        p = build_user_prompt(CTX)
        assert "R$ 1.234,50" in p and "R$ 800,00" in p and "16/11 a 22/11" in p

    def test_texto_fixo_passa_na_propria_checagem(self) -> None:
        assert is_grounded(fallback_text(CTX), allowed_for(CTX))

    def test_texto_fiel_passa_e_inventado_reprova(self) -> None:
        ok = "Você faturou R$ 1.234,50 e lucrou R$ 800,00 em 7 atendimentos."
        assert is_grounded(ok, allowed_for(CTX))
        bad = "Você faturou R$ 1.234,50 e lucrou R$ 900,00 em 7 atendimentos."
        assert not is_grounded(bad, allowed_for(CTX))

    def test_semana_sem_vendas(self) -> None:
        zero = WeeklyNarrativeContext(
            date(2026, 11, 16), date(2026, 11, 22), Decimal("0"), Decimal("0"), 0, 0
        )
        assert is_grounded(fallback_text(zero), allowed_for(zero))


class TestEndpoint:
    def _summary(self, client, headers) -> dict:
        r = client.get("/api/v1/weekly-summary", headers=headers)
        assert r.status_code == 200, r.text
        return r.json()

    def test_texto_fiel_da_ia_e_aceito(self, client, auth_headers, provider) -> None:
        s = self._summary(client, auth_headers)
        provider.reply = (
            f"Semana de {s['sales_count']} atendimento(s). Bom trabalho!"
        )
        r = client.post("/api/v1/weekly-summary/narrative", headers=auth_headers)
        assert r.status_code == 200, r.text
        assert r.json()["source"] == "ai"
        assert provider.calls and "Período" in provider.calls[0]["user"]

    def test_numero_inventado_vira_texto_fixo(
        self, client, auth_headers, provider
    ) -> None:
        provider.reply = "Você faturou R$ 99.999,99 esta semana!"
        r = client.post("/api/v1/weekly-summary/narrative", headers=auth_headers)
        body = r.json()
        assert body["source"] == "fallback"
        assert "99.999" not in body["text"]

    def test_erro_do_provedor_nao_quebra(self, client, auth_headers, provider) -> None:
        provider.fail = True
        r = client.post("/api/v1/weekly-summary/narrative", headers=auth_headers)
        assert r.status_code == 200 and r.json()["source"] == "fallback"

    def test_exige_autenticacao(self, client) -> None:
        assert client.post("/api/v1/weekly-summary/narrative").status_code in (401, 403)
