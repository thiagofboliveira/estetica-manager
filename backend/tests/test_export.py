from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

from app.models.financial_settings import PaymentMethod
from app.models.patient import Patient
from app.models.sale import Sale, SaleStatus, SaleType
from app.services.export_service import ExportService


def test_export_patients_csv():
    """Testa geração de CSV de pacientes com delimitador ';' e BOM UTF-8."""
    mock_patient = Patient(
        id=uuid4(),
        name="Maria Silva",
        phone="+5511999998888",
        consent_whatsapp=True,
        created_at=datetime(2026, 8, 1, 10, 0),
    )

    mock_patient_repo = MagicMock()
    mock_patient_repo.list.return_value = [mock_patient]

    svc = ExportService(
        patient_repo=mock_patient_repo,
        sale_repo=MagicMock(),
        session_repo=MagicMock(),
        procedure_repo=MagicMock(),
    )

    csv_content = svc.export_patients_csv()

    assert csv_content.startswith("\ufeff")
    assert "ID;Nome;Telefone;Consentimento WhatsApp;Data de Cadastro" in csv_content
    assert "Maria Silva;+5511999998888;Sim;01/08/2026 10:00" in csv_content


def test_export_sales_csv():
    """Testa geração de CSV de vendas com valores formatados no padrão brasileiro."""
    patient_id = uuid4()
    mock_patient = Patient(id=patient_id, name="Ana Paula")
    mock_sale = Sale(
        id=uuid4(),
        patient_id=patient_id,
        sold_at=date(2026, 8, 15),
        type=SaleType.PACKAGE,
        payment_method=PaymentMethod.CREDIT,
        installments=3,
        items_total=Decimal("1300.00"),
        gross_amount=Decimal("1200.00"),
        discount_amount=Decimal("100.00"),
        fee_applied=Decimal("5.00"),
        fee_amount_applied=Decimal("60.00"),
        split_applied=Decimal("25.00"),
        split_amount_applied=Decimal("300.00"),
        cost_provisioned=Decimal("200.00"),
        cost_realized=Decimal("200.00"),
        net_profit=Decimal("540.00"),
        margin=Decimal("0.4500"),
        status=SaleStatus.ACTIVE,
    )

    mock_patient_repo = MagicMock()
    mock_patient_repo.list.return_value = [mock_patient]

    mock_sale_repo = MagicMock()
    mock_sale_repo.list.return_value = [mock_sale]

    svc = ExportService(
        patient_repo=mock_patient_repo,
        sale_repo=mock_sale_repo,
        session_repo=MagicMock(),
        procedure_repo=MagicMock(),
    )

    csv_content = svc.export_sales_csv()

    assert "ID Venda;Data da Venda;Paciente;Tipo;Forma de Pagamento" in csv_content
    assert "Ana Paula;PACKAGE;CREDIT;3;1200,00;100,00;60,00;300,00;200,00;540,00;45.0%;ACTIVE" in csv_content
