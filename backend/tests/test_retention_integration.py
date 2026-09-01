from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

from app.domain.sales.session_state_machine import SessionStatus
from app.models.procedure import Modality
from app.models.sale import Sale, SaleStatus, SaleType
from app.models.sale_item import SaleItem
from app.models.session import Session
from app.repositories.booking import BookingRepository
from app.repositories.patient import PatientRepository
from app.repositories.procedure import ProcedureRepository
from app.repositories.professional import ProfessionalRepository
from app.repositories.return_opportunity import ReturnOpportunityRepository
from app.repositories.sale import SaleRepository
from app.repositories.sale_item import SaleItemRepository
from app.repositories.session import SessionRepository
from app.schemas.session import SessionUpdate
from app.services.session_service import SessionService


def test_package_does_not_trigger_return_until_last_session():
    """T-045a: Pacote não reativa prematuramente — sessões PENDING restantes
    impedem a geração de oportunidade de retorno até que a última seja concluída."""
    session_repo = MagicMock(spec=SessionRepository)
    sale_item_repo = MagicMock(spec=SaleItemRepository)
    sale_repo = MagicMock(spec=SaleRepository)
    procedure_repo = MagicMock(spec=ProcedureRepository)
    patient_repo = MagicMock(spec=PatientRepository)
    booking_repo = MagicMock(spec=BookingRepository)
    return_opportunity_repo = MagicMock(spec=ReturnOpportunityRepository)
    professional_repo = MagicMock(spec=ProfessionalRepository)

    svc = SessionService(
        session_repo=session_repo,
        sale_item_repo=sale_item_repo,
        sale_repo=sale_repo,
        procedure_repo=procedure_repo,
        patient_repo=patient_repo,
        booking_repo=booking_repo,
        return_opportunity_repo=return_opportunity_repo,
        professional_repo=professional_repo,
    )

    sale_item_id = uuid4()
    s1_id = uuid4()
    s2_id = uuid4()

    s1 = Session(
        id=s1_id,
        sale_item_id=sale_item_id,
        sequence_number=1,
        status=SessionStatus.SCHEDULED,
        modality=Modality.IN_PERSON,
    )
    s2 = Session(
        id=s2_id,
        sale_item_id=sale_item_id,
        sequence_number=2,
        status=SessionStatus.PENDING,
        modality=Modality.IN_PERSON,
    )

    session_repo.get_by_id.return_value = s1
    session_repo.list_for_sale_item.return_value = [s1, s2]

    sale_item = SaleItem(
        id=sale_item_id,
        sale_id=uuid4(),
        procedure_id=uuid4(),
        quantity=2,
        unit_price=Decimal("500.00"),
        unit_cost_estimated=Decimal("150.00"),
        return_interval_applied=30,
    )
    sale_item_repo.get.return_value = sale_item

    # Conclui apenas a 1ª sessão de 2 (a 2ª continua PENDING)
    dto = SessionUpdate(status=SessionStatus.COMPLETED)
    svc.update(s1_id, dto)

    # NÃO deve ter criado oportunidade de retorno ainda
    return_opportunity_repo.add.assert_not_called()

    # Agora simula a conclusão da 2ª sessão (última)
    s1.status = SessionStatus.COMPLETED
    s2.status = SessionStatus.SCHEDULED
    session_repo.get_by_id.return_value = s2
    sale = Sale(
        id=sale_item.sale_id,
        patient_id=uuid4(),
        type=SaleType.PACKAGE,
        status=SaleStatus.ACTIVE,
    )
    sale_repo.get.return_value = sale
    return_opportunity_repo.find_open_for_patient_and_procedure.return_value = []

    svc.update(s2_id, dto)

    # Agora sim deve ter chamado add() para criar a oportunidade
    return_opportunity_repo.add.assert_called_once()
