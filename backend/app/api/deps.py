"""Dependency chain: JWT -> tenant -> sessão.

É impossível obter uma DbSession sem antes ter passado pela validação
do JWT — não existe caminho no código que produza sessão sem tenant.
Rotas públicas (/health) simplesmente não declaram DbSession.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_professional_id
from app.db.session import get_tenant_session
from app.repositories.patient import PatientRepository
from app.repositories.procedure import ProcedureRepository
from app.services.patient_service import PatientService
from app.services.procedure_service import ProcedureService

CurrentProfessional = Annotated[UUID, Depends(get_current_professional_id)]


def _db(professional_id: CurrentProfessional):
    yield from get_tenant_session(professional_id)


DbSession = Annotated[Session, Depends(_db)]


def get_patient_service(
    session: DbSession, professional_id: CurrentProfessional
) -> PatientService:
    return PatientService(PatientRepository(session, professional_id))


def get_procedure_service(
    session: DbSession, professional_id: CurrentProfessional
) -> ProcedureService:
    return ProcedureService(ProcedureRepository(session, professional_id))


PatientSvc = Annotated[PatientService, Depends(get_patient_service)]
ProcedureSvc = Annotated[ProcedureService, Depends(get_procedure_service)]
