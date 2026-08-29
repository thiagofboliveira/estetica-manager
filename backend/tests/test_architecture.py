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
