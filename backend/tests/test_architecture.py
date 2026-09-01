"""Testes que mantêm as invariantes estruturais do código
(ver backend/ENGENHARIA.md §5-6)."""

import pathlib
import re

APP_ROOT = pathlib.Path(__file__).parent.parent / "app"


def test_nenhum_query_cru_fora_do_repositorio():
    """Qualquer .query( ou session.execute(select(...)) fora de
    app/repositories/ é suspeito de escapar do filtro de tenant."""
    ofensores = []
    for py in APP_ROOT.rglob("*.py"):
        if "repositories" in py.parts:
            continue
        texto = py.read_text(encoding="utf-8")
        for n, linha in enumerate(texto.splitlines(), 1):
            if re.search(r"\.query\(|session\.execute\(select\(", linha):
                ofensores.append(f"{py.relative_to(APP_ROOT)}:{n}: {linha.strip()}")
    assert not ofensores, "Query fora do repositório:\n" + "\n".join(ofensores)


def test_nenhuma_rota_tem_professional_id_no_path():
    """/professionals/{pid}/sales é convite a IDOR — o tenant é sempre
    implícito no token, nunca no path."""
    from app.main import app

    ofensores = [
        r.path
        for r in app.routes
        if hasattr(r, "path") and "professional" in r.path.lower()
    ]
    assert not ofensores, f"Rotas com tenant no path: {ofensores}"


def test_core_money_nao_usa_float():
    """float em cálculo monetário é erro de centavo silencioso."""
    texto = (APP_ROOT / "core" / "money.py").read_text(encoding="utf-8")
    # Permite o TypeError que rejeita float explicitamente.
    proibido = re.findall(r"(?<!isinstance\(value, )float\(", texto)
    assert not proibido, f"app/core/money.py usa float(): {proibido}"


def test_dominio_nao_importa_infraestrutura():
    """app/domain/ é o motor de lucro: puro, sem SQLAlchemy, sem
    FastAPI, sem app.models/app.repositories (backend/ENGENHARIA.md §5).
    Um `from app.models` aqui destrói a testabilidade sem banco —
    silenciosamente, só se percebe quando o suite fica lento.

    Checa só linhas de IMPORT de verdade (import/from), não menções em
    docstring/comentário — senão o próprio texto explicando a regra
    dispara o teste."""
    proibidos = ("sqlalchemy", "fastapi", "app.models", "app.repositories")
    ofensores = []
    for py in (APP_ROOT / "domain").rglob("*.py"):
        for n, linha in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
            stripped = linha.strip()
            if not (stripped.startswith("import ") or stripped.startswith("from ")):
                continue
            for termo in proibidos:
                if re.search(rf"\b{re.escape(termo)}\b", stripped):
                    ofensores.append(f"{py.relative_to(APP_ROOT)}:{n}: {stripped}")
    assert not ofensores, "domain/ importa infraestrutura:\n" + "\n".join(ofensores)


def test_dominio_nao_usa_float():
    for py in (APP_ROOT / "domain").rglob("*.py"):
        assert "float(" not in py.read_text(encoding="utf-8"), f"{py} usa float()"


def test_toda_tabela_com_professional_id_tem_rls_nas_migrations():
    """T-046b: Toda migration que cria tabela com professional_id deve
    conter comandos explícitos de RLS para aquela tabela:
    - ALTER TABLE {tabela} ENABLE ROW LEVEL SECURITY
    - ALTER TABLE {tabela} FORCE ROW LEVEL SECURITY
    - CREATE POLICY ... ON {tabela} USING/WITH CHECK (app.professional_id)

    Este teste inspeciona dinamicamente todas as migrações em alembic/versions/."""
    alembic_dir = pathlib.Path(__file__).parent.parent / "alembic" / "versions"
    if not alembic_dir.exists():
        return

    migracao_files = list(alembic_dir.glob("*.py"))
    assert len(migracao_files) > 0, "Nenhuma migration encontrada para verificar"

    for mig_file in migracao_files:
        conteudo = mig_file.read_text(encoding="utf-8")

        # Localiza todas as tabelas criadas no arquivo: op.create_table("nome", ...)
        # Usamos regex para capturar o nome da tabela e o bloco de criação até o próximo op. ou fim da função
        tabelas_criadas = re.findall(r'op\.create_table\(\s*["\']([^"\']+)["\']', conteudo)

        for tabela in tabelas_criadas:
            # Localiza exatamente o bloco de colunas daquela chamada create_table
            padrao_bloco = rf'op\.create_table\(\s*["\']{re.escape(tabela)}["\']\s*,\s*(.*?)(?=\n\s*op\.create_table|\n\s*op\.execute|\n\s*op\.create_index|\Z)'
            match_bloco = re.search(padrao_bloco, conteudo, re.DOTALL)
            if not match_bloco:
                continue

            bloco_tabela = match_bloco.group(1)

            # Verifica se há definição explícita de coluna professional_id
            tem_coluna_professional_id = bool(
                re.search(r'Column\(\s*["\']professional_id["\']', bloco_tabela)
            )

            # Se a tabela tem professional_id, deve ter RLS configurado especificamente para ela
            if tem_coluna_professional_id and tabela != "professionals":
                assert re.search(
                    rf"ALTER\s+TABLE\s+{re.escape(tabela)}\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY",
                    conteudo,
                    re.IGNORECASE,
                ), f"Migration {mig_file.name} cria tabela '{tabela}' com professional_id mas não executa ENABLE ROW LEVEL SECURITY nela."

                assert re.search(
                    rf"ALTER\s+TABLE\s+{re.escape(tabela)}\s+FORCE\s+ROW\s+LEVEL\s+SECURITY",
                    conteudo,
                    re.IGNORECASE,
                ), f"Migration {mig_file.name} cria tabela '{tabela}' com professional_id mas não executa FORCE ROW LEVEL SECURITY nela."

                assert re.search(
                    rf"CREATE\s+POLICY\s+\w+\s+ON\s+{re.escape(tabela)}",
                    conteudo,
                    re.IGNORECASE,
                ), f"Migration {mig_file.name} cria tabela '{tabela}' com professional_id mas não cria POLICY específica nela."

                assert "app.professional_id" in conteudo, (
                    f"Migration {mig_file.name} não utiliza o setting 'app.professional_id' na definição de segurança."
                )


