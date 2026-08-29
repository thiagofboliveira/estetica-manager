"""Base de todo schema de request/response.

extra="forbid" faz um campo indesejado (ex: professional_id vindo do
cliente) explodir em 422 em vez de ser ignorado em silêncio. Ignorar em
silêncio esconde tanto ataque quanto bug de cliente.
"""

from pydantic import BaseModel, ConfigDict


class InputSchema(BaseModel):
    """Base de todo schema de ENTRADA (request body).

    NUNCA declare professional_id aqui — ele vem do JWT (ver
    app/core/security.py), nunca do corpo do request. Um teste de
    arquitetura garante isso (tests/test_schemas_sem_tenant.py).
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class OutputSchema(BaseModel):
    """Base de todo schema de SAÍDA (response). from_attributes permite
    construir direto de um modelo SQLAlchemy."""

    model_config = ConfigDict(from_attributes=True)
