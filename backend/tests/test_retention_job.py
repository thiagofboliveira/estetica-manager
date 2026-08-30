from unittest.mock import MagicMock
from uuid import uuid4

from app.jobs.retention_health import run_retention_health_check
from app.models.professional import Professional


def test_retention_health_check_success():
    prof1_id = uuid4()
    prof2_id = uuid4()
    prof1 = Professional(id=prof1_id, name="Dra. Ana", timezone="America/Sao_Paulo")
    prof2 = Professional(id=prof2_id, name="Dra. Beatriz", timezone="America/Sao_Paulo")

    admin_session = MagicMock()
    admin_session.scalars.return_value.all.return_value = [prof1, prof2]

    tenant_session_1 = MagicMock()
    tenant_session_1.scalars.return_value.one_or_none.return_value = prof1
    tenant_session_1.scalars.return_value.all.return_value = []
    tenant_session_2 = MagicMock()
    tenant_session_2.scalars.return_value.one_or_none.return_value = prof2
    tenant_session_2.scalars.return_value.all.return_value = []

    def db_session_factory(prof_id):
        return tenant_session_1 if prof_id == prof1_id else tenant_session_2

    report = run_retention_health_check(db_session_factory, admin_session)

    assert report.success is True
    assert report.tenants_processed == 2
    assert len(report.failures) == 0
    assert len(report.stats) == 2


def test_retention_health_check_records_failure_alert():
    prof1_id = uuid4()
    prof1 = Professional(id=prof1_id, name="Dra. Falha", timezone="America/Sao_Paulo")

    admin_session = MagicMock()
    admin_session.scalars.return_value.all.return_value = [prof1]

    def failing_session_factory(prof_id):
        raise ConnectionError("Falha na conexão com banco do tenant")

    report = run_retention_health_check(failing_session_factory, admin_session)

    assert report.success is False
    assert report.tenants_processed == 0
    assert len(report.failures) == 1
    assert "Falha na conexão com banco do tenant" in report.failures[0]
