import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.patient import PatientRepository
from app.repositories.procedure import ProcedureRepository
from app.repositories.professional import ProfessionalRepository
from app.repositories.return_opportunity import ReturnOpportunityRepository
from app.services.retention_service import RetentionService

logger = logging.getLogger("estetica.cron.retention")


@dataclass
class TenantRetentionStats:
    professional_id: UUID
    cards_count: int
    total_potential_value: str
    error: str | None = None


@dataclass
class RetentionHealthReport:
    executed_at: datetime
    success: bool
    tenants_processed: int
    stats: list[TenantRetentionStats] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)


def run_retention_health_check(
    db_session_factory: Callable[[UUID], Session],
    admin_session: Session,
) -> RetentionHealthReport:
    """
    Job de integridade do motor de retorno (TASK-047a, MVP v6 §14, §15).
    Executa a verificação diária em cada tenant ativo para garantir que
    o motor de retenção está operacional e não em silêncio por falha.
    """
    now = datetime.now(UTC)
    report = RetentionHealthReport(executed_at=now, success=True, tenants_processed=0)

    try:
        # Busca todas as profissionais cadastradas via repositório
        prof_repo_admin = ProfessionalRepository(admin_session, UUID(int=0))
        professionals = prof_repo_admin.list_all()
    except Exception as exc:
        msg = f"CRITICAL: Falha ao listar profissionais para check de retenção: {exc}"
        logger.critical(msg, exc_info=True)
        report.success = False
        report.failures.append(msg)
        return report

    for prof in professionals:
        tenant_session = None
        try:
            tenant_session = db_session_factory(prof.id)
            opp_repo = ReturnOpportunityRepository(tenant_session, prof.id)
            patient_repo = PatientRepository(tenant_session, prof.id)
            proc_repo = ProcedureRepository(tenant_session, prof.id)
            prof_repo = ProfessionalRepository(tenant_session, prof.id)

            svc = RetentionService(
                return_opportunity_repo=opp_repo,
                patient_repo=patient_repo,
                procedure_repo=proc_repo,
                professional_repo=prof_repo,
            )

            cards = svc.list_cards()
            total_val = sum((c.total_potential_value for c in cards), start=0)

            report.stats.append(
                TenantRetentionStats(
                    professional_id=prof.id,
                    cards_count=len(cards),
                    total_potential_value=str(total_val),
                )
            )
            report.tenants_processed += 1
        except Exception as exc:
            msg = (
                f"ALERT: Falha no motor de retenção para profissional {prof.id}: {exc}"
            )
            logger.error(msg, exc_info=True)
            report.success = False
            report.failures.append(msg)
            report.stats.append(
                TenantRetentionStats(
                    professional_id=prof.id,
                    cards_count=0,
                    total_potential_value="0.00",
                    error=str(exc),
                )
            )
        finally:
            if tenant_session:
                tenant_session.close()

    if not report.success:
        logger.critical(
            "Alerta de observabilidade: Ocorreram falhas no cron de retenção (%d falhas de %d tenants)",
            len(report.failures),
            len(professionals),
        )
    else:
        logger.info(
            "Cron de retenção executado com sucesso: %d tenants processados.",
            report.tenants_processed,
        )

    return report
