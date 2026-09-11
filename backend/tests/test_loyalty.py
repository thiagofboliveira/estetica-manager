from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.domain.loyalty.rules import VipTier
from app.models.financial_settings import FinancialSettings
from app.models.loyalty import LoyaltyTransaction, LoyaltyTransactionType
from app.models.patient import Patient
from app.models.sale import Sale, SaleStatus
from app.repositories.financial_settings import FinancialSettingsRepository
from app.repositories.loyalty_repository import LoyaltyRepository
from app.repositories.patient import PatientRepository
from app.repositories.professional import ProfessionalRepository
from app.schemas.loyalty import LoyaltyAdjustRequest
from app.services.loyalty_service import InsufficientPointsError, LoyaltyService


@pytest.fixture
def mock_loyalty_repo():
    return MagicMock(spec=LoyaltyRepository)


@pytest.fixture
def mock_patient_repo():
    return MagicMock(spec=PatientRepository)


@pytest.fixture
def mock_settings_repo():
    repo = MagicMock(spec=FinancialSettingsRepository)
    settings = FinancialSettings(
        loyalty_enabled=True,
        loyalty_points_per_currency=Decimal("0.10"),
        loyalty_redemption_rate=Decimal("1.00"),
        referral_reward_points=50,
    )
    repo.get_singleton.return_value = settings
    return repo


@pytest.fixture
def mock_professional_repo():
    repo = MagicMock(spec=ProfessionalRepository)
    prof = MagicMock()
    prof.name = "Dra. Juliana Estética"
    repo.get_current.return_value = prof
    return repo


def test_get_patient_loyalty_creates_code_if_missing(
    mock_loyalty_repo, mock_patient_repo, mock_settings_repo, mock_professional_repo
):
    patient_id = uuid4()
    patient = Patient(
        id=patient_id,
        name="Camila Santos",
        loyalty_points=150,
        vip_tier="SILVER",
        referral_code=None,
        referred_by_id=None,
    )
    mock_patient_repo.get.return_value = patient
    mock_loyalty_repo.list_for_patient.return_value = []

    svc = LoyaltyService(
        loyalty_repo=mock_loyalty_repo,
        patient_repo=mock_patient_repo,
        settings_repo=mock_settings_repo,
        professional_repo=mock_professional_repo,
    )
    out = svc.get_patient_loyalty(patient_id)

    assert out.patient_name == "Camila Santos"
    assert out.loyalty_points == 150
    assert out.vip_tier == VipTier.SILVER
    assert out.vip_badge == "🥈"
    assert out.monetary_value == Decimal("150.00")
    assert out.referral_code is not None
    assert out.referral_code.startswith("CAM-")


def test_adjust_points_credit_and_debit(
    mock_loyalty_repo, mock_patient_repo, mock_settings_repo
):
    patient_id = uuid4()
    patient = Patient(
        id=patient_id,
        name="Beatriz Lima",
        loyalty_points=50,
        vip_tier="BRONZE",
    )
    mock_patient_repo.get.return_value = patient

    tx = LoyaltyTransaction(
        id=uuid4(),
        patient_id=patient_id,
        points=60,
        balance_after=110,
        transaction_type="ADJUSTMENT",
        description="Bônus de aniversário",
    )
    mock_loyalty_repo.add_transaction.return_value = tx

    svc = LoyaltyService(
        loyalty_repo=mock_loyalty_repo,
        patient_repo=mock_patient_repo,
        settings_repo=mock_settings_repo,
    )

    # 1. Crédito que promove para SILVER (110 pts)
    req = LoyaltyAdjustRequest(points=60, description="Bônus de aniversário")
    res = svc.adjust_points(patient_id, req)
    assert patient.loyalty_points == 110
    assert patient.vip_tier == VipTier.SILVER
    assert res.balance_after == 110

    # 2. Débito com saldo insuficiente deve lançar erro
    req_debit = LoyaltyAdjustRequest(points=-200, description="Tentativa de resgate excessivo")
    with pytest.raises(InsufficientPointsError):
        svc.adjust_points(patient_id, req_debit)


def test_process_sale_points_accrual_and_referral_reward(
    mock_loyalty_repo, mock_patient_repo, mock_settings_repo
):
    referrer_id = uuid4()
    referrer = Patient(
        id=referrer_id,
        name="Paula Amiga",
        loyalty_points=100,
        vip_tier="SILVER",
    )

    buyer_id = uuid4()
    buyer = Patient(
        id=buyer_id,
        name="Fernanda Nova",
        loyalty_points=0,
        vip_tier="BRONZE",
        referred_by_id=referrer_id,
    )

    def get_patient(pid):
        if pid == referrer_id:
            return referrer
        if pid == buyer_id:
            return buyer
        return None

    mock_patient_repo.get.side_effect = get_patient

    sale = Sale(
        id=uuid4(),
        patient_id=buyer_id,
        gross_amount=Decimal("400.00"),
        status=SaleStatus.ACTIVE,
    )

    svc = LoyaltyService(
        loyalty_repo=mock_loyalty_repo,
        patient_repo=mock_patient_repo,
        settings_repo=mock_settings_repo,
    )

    earned = svc.process_sale_points(sale, buyer)

    # R$ 400 * 0.10 = 40 pontos para a compradora
    assert earned == 40
    assert buyer.loyalty_points == 40
    # Referrer ganha bônus de 50 pontos (100 + 50 = 150)
    assert referrer.loyalty_points == 150

    # 2 chamadas de add_transaction: uma para a compradora, outra para a amiga que indicou
    assert mock_loyalty_repo.add_transaction.call_count == 2


def test_referral_info_generates_whatsapp_link(
    mock_loyalty_repo, mock_patient_repo, mock_settings_repo, mock_professional_repo
):
    patient_id = uuid4()
    patient = Patient(
        id=patient_id,
        name="Larissa Manoela",
        loyalty_points=80,
        vip_tier="BRONZE",
        referral_code="LAR-9921",
    )
    mock_patient_repo.get.return_value = patient
    mock_patient_repo.list_referred_by.return_value = []

    svc = LoyaltyService(
        loyalty_repo=mock_loyalty_repo,
        patient_repo=mock_patient_repo,
        settings_repo=mock_settings_repo,
        professional_repo=mock_professional_repo,
    )
    info = svc.get_referral_info(patient_id)

    assert info.referral_code == "LAR-9921"
    assert "LAR-9921" in info.whatsapp_share_text
    assert "Dra. Juliana Estética" in info.whatsapp_share_text
    assert info.whatsapp_share_url.startswith("https://wa.me/?text=")
