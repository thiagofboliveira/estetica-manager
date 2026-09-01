"""Catálogo de Templates de Procedimentos Sugeridos de Mercado (EPIC-S2-04, TASK-BACK-S2-18).

Constantes do domínio para acelerar o onboarding da profissional com valores de referência.
Invariante I1: Valores monetários em Decimal.
Invariante I7: Marcados como sugeridos.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ProcedureTemplateData:
    template_id: str
    name: str
    type: str  # "SERVICE"
    suggested_price: Decimal
    suggested_cost: Decimal
    suggested_return_interval_days: int | None
    category: str
    is_suggested: bool = True


PROCEDURE_TEMPLATES: list[ProcedureTemplateData] = [
    ProcedureTemplateData(
        template_id="limpeza-de-pele",
        name="Limpeza de Pele",
        type="SERVICE",
        suggested_price=Decimal("180.00"),
        suggested_cost=Decimal("30.00"),
        suggested_return_interval_days=30,
        category="Facial",
    ),
    ProcedureTemplateData(
        template_id="peeling-quimico",
        name="Peeling Químico",
        type="SERVICE",
        suggested_price=Decimal("250.00"),
        suggested_cost=Decimal("45.00"),
        suggested_return_interval_days=21,
        category="Facial",
    ),
    ProcedureTemplateData(
        template_id="microagulhamento",
        name="Microagulhamento",
        type="SERVICE",
        suggested_price=Decimal("350.00"),
        suggested_cost=Decimal("80.00"),
        suggested_return_interval_days=30,
        category="Facial",
    ),
    ProcedureTemplateData(
        template_id="tratamento-acne",
        name="Tratamento de Acne — Sessão",
        type="SERVICE",
        suggested_price=Decimal("280.00"),
        suggested_cost=Decimal("50.00"),
        suggested_return_interval_days=15,
        category="Facial",
    ),
    ProcedureTemplateData(
        template_id="botox",
        name="Botox — Aplicação",
        type="SERVICE",
        suggested_price=Decimal("800.00"),
        suggested_cost=Decimal("350.00"),
        suggested_return_interval_days=120,
        category="Injetáveis",
    ),
    ProcedureTemplateData(
        template_id="preenchimento-labial",
        name="Preenchimento Labial",
        type="SERVICE",
        suggested_price=Decimal("1200.00"),
        suggested_cost=Decimal("550.00"),
        suggested_return_interval_days=180,
        category="Injetáveis",
    ),
    ProcedureTemplateData(
        template_id="drenagem-linfatica",
        name="Drenagem Linfática",
        type="SERVICE",
        suggested_price=Decimal("150.00"),
        suggested_cost=Decimal("20.00"),
        suggested_return_interval_days=7,
        category="Corporal",
    ),
    ProcedureTemplateData(
        template_id="massagem-modeladora",
        name="Massagem Modeladora",
        type="SERVICE",
        suggested_price=Decimal("180.00"),
        suggested_cost=Decimal("25.00"),
        suggested_return_interval_days=7,
        category="Corporal",
    ),
    ProcedureTemplateData(
        template_id="depilacao-laser",
        name="Depilação a Laser — Sessão",
        type="SERVICE",
        suggested_price=Decimal("200.00"),
        suggested_cost=Decimal("40.00"),
        suggested_return_interval_days=30,
        category="Corporal",
    ),
    ProcedureTemplateData(
        template_id="revitalizacao-facial",
        name="Revitalização Facial",
        type="SERVICE",
        suggested_price=Decimal("300.00"),
        suggested_cost=Decimal("60.00"),
        suggested_return_interval_days=30,
        category="Facial",
    ),
]


def list_procedure_templates() -> list[ProcedureTemplateData]:
    return list(PROCEDURE_TEMPLATES)


def find_procedure_template(template_id: str) -> ProcedureTemplateData | None:
    for t in PROCEDURE_TEMPLATES:
        if t.template_id == template_id:
            return t
    return None
