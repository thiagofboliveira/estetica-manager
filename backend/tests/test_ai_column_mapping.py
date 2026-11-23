# ruff: noqa: F811
"""AI-08 — mapeamento de colunas de planilha (a IA só aponta colunas)."""

from app.domain.ai.column_mapping import (
    build_user_prompt,
    heuristic_mapping,
    is_confident,
    mask_value,
    merge,
    parse_ai_mapping,
)
from tests.test_ai_draft_message import (  # noqa: F401
    auth_headers,
    client,
    professional_id,
    provider,
)

URL = "/api/v1/ai/import/map-columns"


class TestHeuristic:
    def test_cabecalhos_comuns_em_portugues(self) -> None:
        m = heuristic_mapping(["Nome", "WhatsApp", "E-mail", "Observações", "Última visita"])
        assert m == {
            "name": 0, "phone": 1, "email": 2, "notes": 3, "last_visit_date": 4,
        }
        assert is_confident(m)

    def test_ultima_visita_nao_vira_nome(self) -> None:
        m = heuristic_mapping(["Cliente", "Celular", "Última visita"])
        assert m["name"] == 0 and m["last_visit_date"] == 2

    def test_cabecalho_estranho_nao_e_confiante(self) -> None:
        assert not is_confident(heuristic_mapping(["Col A", "Col B"]))


class TestPrivacy:
    def test_mascara_esconde_letras_e_digitos(self) -> None:
        assert mask_value("Maria Silva (11) 99999-1234") == "Aaaaa Aaaaa (99) 99999-9999"

    def test_prompt_nao_contem_dado_real(self) -> None:
        prompt = build_user_prompt(
            ["A", "B"], [["Maria Silva", "31988887777"], ["Ana", "11977776666"]]
        )
        for secret in ("Maria", "Silva", "31988887777", "11977776666", "Ana"):
            assert secret not in prompt


class TestParse:
    def test_json_valido(self) -> None:
        r = parse_ai_mapping('{"name": 0, "phone": 2, "email": null}', 3)
        assert r is not None and r["name"] == 0 and r["phone"] == 2

    def test_rejeita_indice_fora_repetido_ou_tipo_errado(self) -> None:
        assert parse_ai_mapping('{"name": 5}', 3) is None
        assert parse_ai_mapping('{"name": 1, "phone": 1}', 3) is None
        assert parse_ai_mapping('{"name": "0"}', 3) is None
        assert parse_ai_mapping("não sei", 3) is None

    def test_heuristica_manda_ia_so_completa(self) -> None:
        h = {"name": 0, "phone": None, "email": None, "notes": None, "last_visit_date": None}
        a = {"name": 1, "phone": 2, "email": None, "notes": None, "last_visit_date": None}
        assert merge(h, a)["name"] == 0 and merge(h, a)["phone"] == 2


class TestEndpoint:
    def test_cabecalho_claro_nao_chama_ia(self, client, auth_headers, provider) -> None:
        r = client.post(URL, json={"headers": ["Nome", "Telefone"]}, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["name"] == 0 and r.json()["phone"] == 1
        assert provider.calls == []

    def test_cabecalho_confuso_usa_ia_sem_enviar_dados(
        self, client, auth_headers, provider
    ) -> None:
        provider.reply = '{"name": 0, "phone": 1}'
        r = client.post(
            URL,
            json={"headers": ["X1", "X2"], "sample_rows": [["Maria Souza", "31999990000"]]},
            headers=auth_headers,
        )
        body = r.json()
        assert body["source"] == "ai" and body["name"] == 0 and body["phone"] == 1
        assert "Maria" not in provider.calls[0]["user"]
        assert "31999990000" not in provider.calls[0]["user"]

    def test_resposta_invalida_da_ia_cai_na_heuristica(
        self, client, auth_headers, provider
    ) -> None:
        provider.reply = '{"name": 9}'
        r = client.post(URL, json={"headers": ["X1", "X2"]}, headers=auth_headers)
        assert r.json()["source"] == "fallback" and r.json()["name"] is None

    def test_limites_e_autenticacao(self, client, auth_headers) -> None:
        assert client.post(URL, json={"headers": []}, headers=auth_headers).status_code == 422
        too_many = {"headers": [f"c{i}" for i in range(51)]}
        assert client.post(URL, json=too_many, headers=auth_headers).status_code == 422
        assert client.post(URL, json={"headers": ["Nome"]}).status_code in (401, 403)
