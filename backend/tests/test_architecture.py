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
        texto = py.read_text()
        for n, linha in enumerate(texto.splitlines(), 1):
            if re.search(r"\.query\(|session\.execute\(select\(", linha):
                ofensores.append(f"{py.relative_to(APP_ROOT)}:{n}: {linha.strip()}")
    assert not ofensores, "Query fora do repositório:\n" + "\n".join(ofensores)


def test_nenhuma_rota_tem_professional_id_no_path():
    """/professionals/{pid}/sales é convite a IDOR — o tenant é sempre
    implícito no token, nunca no path."""
    from app.main import app

    ofensores = [
        r.path for r in app.routes if hasattr(r, "path") and "professional" in r.path.lower()
    ]
    assert not ofensores, f"Rotas com tenant no path: {ofensores}"


def test_core_money_nao_usa_float():
    """float em cálculo monetário é erro de centavo silencioso."""
    texto = (APP_ROOT / "core" / "money.py").read_text()
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
        for n, linha in enumerate(py.read_text().splitlines(), 1):
            stripped = linha.strip()
            if not (stripped.startswith("import ") or stripped.startswith("from ")):
                continue
            for termo in proibidos:
                if re.search(rf"\b{re.escape(termo)}\b", stripped):
                    ofensores.append(
                        f"{py.relative_to(APP_ROOT)}:{n}: {stripped}"
                    )
    assert not ofensores, "domain/ importa infraestrutura:\n" + "\n".join(ofensores)


def test_dominio_nao_usa_float():
    for py in (APP_ROOT / "domain").rglob("*.py"):
        assert "float(" not in py.read_text(), f"{py} usa float()"
