"""Integration tests for the Billing API endpoints (Asaas integration)."""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

pytestmark = pytest.mark.skipif(
    not settings.DEV_AUTH_SECRET, reason="requer DEV_AUTH_SECRET + Postgres real"
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    resp = client.post("/dev/login")
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


class TestBillingPlansEndpoint:
    def test_get_plans_public_returns_centralized_pricing(self, client: TestClient):
        """GET /api/v1/billing/plans should be public and return 3 pricing cycles."""
        resp = client.get("/api/v1/billing/plans")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        plan = data[0]
        assert plan["id"] == "pro"
        assert plan["trial_days"] == 14
        assert "Inauguração" in plan["promo_badge"]
        assert len(plan["cycles"]) == 3

        cycles = {c["cycle"]: c for c in plan["cycles"]}
        assert "MONTHLY" in cycles
        assert "QUARTERLY" in cycles
        assert "YEARLY" in cycles

        assert Decimal(cycles["MONTHLY"]["total_amount"]) == Decimal("80.00")
        assert Decimal(cycles["QUARTERLY"]["monthly_equivalent"]) == Decimal("65.00")
        assert Decimal(cycles["QUARTERLY"]["total_amount"]) == Decimal("195.00")
        assert Decimal(cycles["YEARLY"]["monthly_equivalent"]) == Decimal("50.00")
        assert Decimal(cycles["YEARLY"]["total_amount"]) == Decimal("600.00")
        assert Decimal(cycles["YEARLY"]["savings_percentage"]) == Decimal("37.50")


class TestCouponValidationEndpoint:
    def test_validate_seeded_coupon(self, client: TestClient, auth_headers: dict[str, str]):
        """POST /api/v1/billing/coupons/validate with INAUGURACAO coupon."""
        resp = client.post(
            "/api/v1/billing/coupons/validate",
            json={"code": "inauguracao", "cycle": "monthly"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is True
        assert data["code"] == "INAUGURACAO"
        assert data["discount_type"] == "PERCENTAGE"
        assert Decimal(data["discount_amount"]) == Decimal("8.00")
        assert Decimal(data["final_amount"]) == Decimal("72.00")

    def test_validate_invalid_coupon(self, client: TestClient, auth_headers: dict[str, str]):
        resp = client.post(
            "/api/v1/billing/coupons/validate",
            json={"code": "NAO_EXISTE_999", "cycle": "monthly"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is False
        assert "não encontrado" in data["message"].lower()


class TestBillingStatusEndpoint:
    def test_get_billing_status_authenticated(self, client: TestClient, auth_headers: dict[str, str]):
        """GET /api/v1/billing/status returns trial status or subscription."""
        resp = client.get("/api/v1/billing/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "is_trial_active" in data
        assert "days_left_in_trial" in data
        assert data["plan_id"] == "clinic_pro" or data["plan_id"] == "pro"


class TestCheckoutEndpoint:
    def test_checkout_creates_subscription_with_trial_due_date(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        """POST /api/v1/billing/checkout creates Asaas subscription and preserves trial."""
        payload = {
            "cycle": "QUARTERLY",
            "coupon_code": "INAUGURACAO",
            "billing_type": "CREDIT_CARD",
        }
        resp = client.post("/api/v1/billing/checkout", json=payload, headers=auth_headers)
        assert resp.status_code == 200 or resp.status_code == 201
        data = resp.json()
        assert data["cycle"] == "QUARTERLY"
        # 195.00 - 10% = 175.50
        assert Decimal(data["amount"]) == Decimal("175.50")
        assert data["subscription_id"] is not None
        assert data["first_due_date"] is not None


class TestAsaasWebhookEndpoint:
    def test_webhook_unauthorized_without_secret(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setattr(settings, "ASAAS_WEBHOOK_SECRET", "super_secret_webhook_123")
        resp = client.post(
            "/api/v1/billing/webhooks/asaas",
            json={"event": "PAYMENT_CONFIRMED", "payment": {"id": "pay_123"}},
            headers={"asaas-access-token": "wrong_secret"},
        )
        assert resp.status_code == 401

    def test_webhook_authorized_handles_event(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ):
        secret = "super_secret_webhook_123"
        monkeypatch.setattr(settings, "ASAAS_WEBHOOK_SECRET", secret)
        resp = client.post(
            "/api/v1/billing/webhooks/asaas",
            json={
                "event": "PAYMENT_CONFIRMED",
                "payment": {
                    "id": "pay_123",
                    "subscription": "sub_mock_non_existent",
                },
            },
            headers={"asaas-access-token": secret},
        )
        assert resp.status_code == 200
        assert resp.json() == {"status": "received"}
