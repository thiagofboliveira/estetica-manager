from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.money import ZERO
from app.domain.financial.calculator import (
    FeePayer,
    LineItem,
    PaymentMethod,
    SaleParams,
    SplitBase,
    calculate_sale,
)
from app.models.patient import Gender
from app.models.sale import SaleType
from app.schemas.clinic import ClinicCreateInput, ClinicUpdateInput
from app.schemas.loyalty import LoyaltyRewardCreate, LoyaltyRewardUpdate
from app.schemas.patient import (
    PatientBatchImportItem,
    PatientBatchImportRequest,
    PatientCreate,
    PatientUpdate,
)
from app.schemas.sale import SaleCreate, SaleItemCreate, SaleSimulationInput
from app.schemas.session import SessionUpdate


class TestPatientSchemaEdgeCases:
    """Testa robustez de PatientCreate e PatientUpdate contra strings vazias enviadas por formulários web."""

    def test_patient_create_with_empty_strings_coerces_to_none(self) -> None:
        payload = {
            "name": "Maria Silva",
            "phone": "",
            "email": "",
            "birth_date": "",
            "notes": "   ",
            "gender": "",
            "referred_by_id": "",
        }
        patient = PatientCreate(**payload)
        assert patient.name == "Maria Silva"
        assert patient.phone is None
        assert patient.email is None
        assert patient.birth_date is None
        assert patient.notes is None
        assert patient.gender is None
        assert patient.referred_by_id is None

    def test_patient_create_with_valid_optional_values(self) -> None:
        ref_id = uuid4()
        patient = PatientCreate(
            name="Ana Paula",
            phone="(11) 98765-4321",
            email="ana@exemplo.com",
            birth_date="1990-05-15",
            notes="Observação válida",
            gender="FEMALE",
            referred_by_id=str(ref_id),
        )
        assert patient.name == "Ana Paula"
        assert patient.phone == "+5511987654321"
        assert patient.email == "ana@exemplo.com"
        assert patient.birth_date == date(1990, 5, 15)
        assert patient.gender == Gender.FEMALE
        assert patient.referred_by_id == ref_id

    def test_patient_update_with_empty_strings_coerces_to_none(self) -> None:
        payload = {
            "email": "",
            "birth_date": "",
            "notes": "",
            "gender": "",
            "referred_by_id": "",
            "vip_tier": "",
        }
        update = PatientUpdate(**payload)
        assert update.email is None
        assert update.birth_date is None
        assert update.notes is None
        assert update.gender is None
        assert update.referred_by_id is None
        assert update.vip_tier is None

    def test_patient_batch_import_with_empty_strings(self) -> None:
        item = PatientBatchImportItem(
            name="Joana",
            phone="",
            email="",
            notes="",
            procedure_id="",
            last_visit_date="",
        )
        assert item.phone is None
        assert item.email is None
        assert item.notes is None
        assert item.procedure_id is None
        assert item.last_visit_date is None

        req = PatientBatchImportRequest(
            patients=[item],
            default_procedure_id="",
        )
        assert req.default_procedure_id is None


class TestClinicSchemaEdgeCases:
    def test_clinic_create_and_update_with_empty_strings(self) -> None:
        c_create = ClinicCreateInput(
            name="Clínica Estética",
            document="",
            phone="",
            email="",
        )
        assert c_create.document is None
        assert c_create.phone is None
        assert c_create.email is None

        c_update = ClinicUpdateInput(
            name="Novo Nome",
            document="   ",
            phone="",
            email="",
            plan="",
        )
        assert c_update.document is None
        assert c_update.phone is None
        assert c_update.email is None
        assert c_update.plan is None


class TestSaleSchemaAndCalculatorEdgeCases:
    def test_sale_create_empty_discount_defaults_to_zero(self) -> None:
        sale = SaleCreate(
            patient_id=uuid4(),
            type=SaleType.SINGLE,
            items=[SaleItemCreate(procedure_id=uuid4(), quantity=1)],
            payment_method=PaymentMethod.PIX,
            discount_amount="",
            notes="",
            booking_id="",
        )
        assert sale.discount_amount == "0.00"
        assert sale.notes is None
        assert sale.booking_id is None

    def test_sale_create_negative_discount_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            SaleCreate(
                patient_id=uuid4(),
                type=SaleType.SINGLE,
                items=[SaleItemCreate(procedure_id=uuid4(), quantity=1)],
                payment_method=PaymentMethod.PIX,
                discount_amount="-10.00",
            )
        assert "Desconto não pode ser negativo" in str(exc_info.value)

    def test_sale_simulation_empty_and_negative_discount(self) -> None:
        sim = SaleSimulationInput(
            procedure_id="",
            price="",
            estimated_cost="",
            discount_amount="",
        )
        assert sim.procedure_id is None
        assert sim.price is None
        assert sim.estimated_cost is None
        assert sim.discount_amount == "0.00"

        with pytest.raises(ValidationError):
            SaleSimulationInput(discount_amount="-5.00")

    def test_calculate_sale_rejects_negative_discount(self) -> None:
        item = LineItem(
            unit_price=Decimal("100.00"),
            quantity=1,
            unit_cost_estimated=Decimal("20.00"),
            session_costs=[Decimal("20.00")],
        )
        params = SaleParams(
            split_clinic_percentage=ZERO,
            split_base=SplitBase.GROSS,
            fee_payer=FeePayer.PROFESSIONAL,
            payment_method=PaymentMethod.PIX,
            installments=1,
            discount_amount=Decimal("-10.00"),
            fee_rules=[],
        )
        with pytest.raises(ValueError, match="desconto não pode ser negativo"):
            calculate_sale([item], params)


class TestSessionAndLoyaltyEdgeCases:
    def test_session_update_empty_strings(self) -> None:
        session_up = SessionUpdate(
            cost_override="",
            notes="   ",
            status="",
        )
        assert session_up.cost_override is None
        assert session_up.notes is None
        assert session_up.status is None

    def test_loyalty_reward_empty_discount_value(self) -> None:
        reward = LoyaltyRewardCreate(
            points_cost=100,
            title="Sessão Cortesia",
            discount_value="",
        )
        assert reward.discount_value is None

        reward_up = LoyaltyRewardUpdate(
            title="Novo Título",
            description="",
            discount_value="",
        )
        assert reward_up.description is None
        assert reward_up.discount_value is None
