"""Nenhum schema de INPUT pode aceitar professional_id do cliente
(ver ../../ENGENHARIA.md invariante I2 e backend/ENGENHARIA.md §2)."""

import inspect

import app.schemas.patient as patient_schemas
import app.schemas.procedure as procedure_schemas
from app.schemas.base import InputSchema

MODULES_COM_SCHEMAS = [patient_schemas, procedure_schemas]


def test_nenhum_schema_de_input_aceita_professional_id():
    verificados = 0
    for module in MODULES_COM_SCHEMAS:
        for _, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, InputSchema)
                and obj is not InputSchema
            ):
                verificados += 1
                assert "professional_id" not in obj.model_fields, (
                    f"{obj.__name__} aceita professional_id do cliente — "
                    "deve vir do claim sub do JWT, nunca do body"
                )
    assert verificados > 0, "nenhum InputSchema encontrado — teste não está cobrindo nada"
