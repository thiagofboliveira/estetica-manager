from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.domain.catalog.procedure_templates import (
    find_procedure_template,
    list_procedure_templates,
)
from app.models.procedure import Procedure
from app.schemas.procedure import ProcedureFromTemplateCreate
from app.services.procedure_service import (
    ProcedureAlreadyExistsError,
    ProcedureService,
)


def test_list_procedure_templates():
    """Testa catálogo de templates contendo pelo menos 10 procedimentos com dados válidos."""
    templates = list_procedure_templates()
    assert len(templates) >= 10

    # Verifica campos do template Limpeza de Pele
    limpeza = find_procedure_template("limpeza-de-pele")
    assert limpeza is not None
    assert limpeza.name == "Limpeza de Pele"
    assert limpeza.suggested_price == Decimal("180.00")
    assert limpeza.suggested_cost == Decimal("30.00")
    assert limpeza.suggested_return_interval_days == 30
    assert limpeza.category == "Facial"
    assert limpeza.is_suggested is True


def test_create_from_template_defaults():
    """Testa criação de procedimento usando os valores sugeridos do template."""
    mock_repo = MagicMock()
    mock_repo.find_by_name.return_value = None

    created_entity = None

    def fake_add(p):
        nonlocal created_entity
        p.id = uuid4()
        created_entity = p
        return p

    mock_repo.add.side_effect = fake_add

    svc = ProcedureService(mock_repo)

    req = ProcedureFromTemplateCreate(template_id="botox")
    res = svc.create_from_template(req)

    assert res.name == "Botox — Aplicação"
    assert res.price == Decimal("800.00")
    assert res.estimated_cost == Decimal("350.00")
    assert res.return_interval_days == 120
    mock_repo.add.assert_called_once()


def test_create_from_template_with_overrides():
    """Testa criação aplicando overrides de preço, custo e intervalo de retorno."""
    mock_repo = MagicMock()
    mock_repo.find_by_name.return_value = None

    def fake_add(p):
        p.id = uuid4()
        return p

    mock_repo.add.side_effect = fake_add

    svc = ProcedureService(mock_repo)

    req = ProcedureFromTemplateCreate(
        template_id="peeling-quimico",
        name="Peeling de Diamante Especial",
        price="290.00",
        estimated_cost="55.00",
        return_interval_days=28,
    )
    res = svc.create_from_template(req)

    assert res.name == "Peeling de Diamante Especial"
    assert res.price == Decimal("290.00")
    assert res.estimated_cost == Decimal("55.00")
    assert res.return_interval_days == 28


def test_create_from_template_duplicate_conflict():
    """Tentar criar com nome já existente deve disparar ProcedureAlreadyExistsError."""
    mock_repo = MagicMock()
    mock_repo.find_by_name.return_value = Procedure(
        id=uuid4(),
        professional_id=uuid4(),
        name="Limpeza de Pele",
        price=Decimal("180.00"),
        estimated_cost=Decimal("30.00"),
    )

    svc = ProcedureService(mock_repo)

    req = ProcedureFromTemplateCreate(template_id="limpeza-de-pele")

    with pytest.raises(ProcedureAlreadyExistsError, match="já está cadastrado"):
        svc.create_from_template(req)
