# ruff: noqa: F811
"""AI-04 — alerta de procedimento no prejuízo (regra do backend + texto da IA)."""

import uuid
from decimal import Decimal

from app.domain.ai.grounding import is_grounded
from app.domain.ai.loss_alert import (
    allowed_for,
    build_user_prompt,
    detect_loss_alerts,
    fallback_text,
)
from app.domain.financial.procedure_ranking import ProcedureRankingRow
from tests.test_ai_draft_message import (  # noqa: F401
    auth_headers,
    client,
    professional_id,
    provider,
)


def row(name, revenue, profit, margin, sessions=2):
    return ProcedureRankingRow(
        procedure_id=uuid.uuid4(),
        procedure_name=name,
        gross_revenue=Decimal(revenue),
        net_profit=Decimal(profit),
        margin=None if margin is None else Decimal(margin),
        session_count=sessions,
    )


class TestRule:
    def test_prejuizo_e_margem_baixa_entram_os_saudaveis_nao(self) -> None:
        rows = [
            row("Saudável", "1000.00", "500.00", "0.50"),
            row("Baixa", "1000.00", "100.00", "0.10"),
            row("Prejuízo", "500.00", "-50.00", "-0.10"),
        ]
        alerts = detect_loss_alerts(rows)
        assert [a.procedure_name for a in alerts] == ["Prejuízo", "Baixa"]
        assert [a.kind for a in alerts] == ["loss", "low_margin"]

    def test_exatamente_no_limite_nao_alerta(self) -> None:
        assert detect_loss_alerts([row("Limite", "1000.00", "150.00", "0.15")]) == []

    def test_sem_margem_calculavel_nao_gera_alerta(self) -> None:
        assert detect_loss_alerts([row("Sem receita", "0.00", "0.00", None)]) == []

    def test_no_maximo_tres_os_piores_primeiro(self) -> None:
        rows = [row(f"P{i}", "100.00", f"-{i}.00", "-0.05") for i in range(1, 6)]
        alerts = detect_loss_alerts(rows)
        assert len(alerts) == 3
        assert alerts[0].net_profit == Decimal("-5.00")

    def test_margem_vira_percentual_inteiro(self) -> None:
        a = detect_loss_alerts([row("X", "1000.00", "125.00", "0.125")])[0]
        assert a.margin_percent == 13  # arredonda meio para cima


class TestGrounding:
    def test_texto_fixo_e_prompt_passam_na_checagem(self) -> None:
        alerts = detect_loss_alerts(
            [row("Peeling 2", "1234.50", "-80.00", "-0.0648", 4)]
        )
        assert is_grounded(fallback_text(alerts), allowed_for(alerts))
        assert "R$ 1.234,50" in build_user_prompt(alerts)

    def test_valor_inventado_reprova(self) -> None:
        alerts = detect_loss_alerts([row("Peeling", "1000.00", "-80.00", "-0.08")])
        assert not is_grounded("Você perdeu R$ 999,00 no Peeling.", allowed_for(alerts))


class TestEndpoints:
    def test_lista_alertas_sem_ia(self, client, auth_headers, provider) -> None:
        r = client.get("/api/v1/reports/procedures/loss-alerts", headers=auth_headers)
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body["alerts"], list) and len(body["alerts"]) <= 3
        assert provider.calls == []  # o alerta nunca chama a IA

    def test_periodo_invalido_422(self, client, auth_headers, provider) -> None:
        r = client.get(
            "/api/v1/reports/procedures/loss-alerts",
            params={"period": "xyz"},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_explicacao_sem_alertas_404_e_nao_chama_ia(
        self, client, auth_headers, provider, monkeypatch
    ) -> None:
        import app.api.v1.reports as reports

        monkeypatch.setattr(reports, "detect_loss_alerts", lambda rows: [])
        r = client.post(
            "/api/v1/reports/procedures/loss-alerts/explanation", headers=auth_headers
        )
        assert r.status_code == 404
        assert provider.calls == []

    def test_explicacao_com_alerta_usa_ia_e_barra_numero_inventado(
        self, client, auth_headers, provider, monkeypatch
    ) -> None:
        import app.api.v1.reports as reports

        alerts = detect_loss_alerts([row("Peeling", "1000.00", "-80.00", "-0.08")])
        monkeypatch.setattr(reports, "detect_loss_alerts", lambda rows: alerts)
        url = "/api/v1/reports/procedures/loss-alerts/explanation"

        provider.reply = "O Peeling teve prejuízo de R$ 80,00. Revise o custo dos insumos."
        ok = client.post(url, headers=auth_headers).json()
        assert ok["source"] == "ai"

        provider.reply = "O Peeling perdeu R$ 777,00. Revise o custo."
        bad = client.post(url, headers=auth_headers).json()
        assert bad["source"] == "fallback"
        assert "777" not in bad["text"]

    def test_exige_autenticacao(self, client) -> None:
        assert client.get("/api/v1/reports/procedures/loss-alerts").status_code in (401, 403)
        assert client.post(
            "/api/v1/reports/procedures/loss-alerts/explanation"
        ).status_code in (401, 403)
