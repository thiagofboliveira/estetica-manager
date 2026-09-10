"""Cliente HTTP de integração com a API v3 do Asaas (Gateway de Pagamento)."""

from datetime import date
from decimal import Decimal
import logging
from uuid import uuid4

import httpx

from app.core.config import settings
from app.domain.billing.pricing import BillingCycle

logger = logging.getLogger(__name__)


class AsaasError(Exception):
    """Erro retornado pela API do Asaas."""

    def __init__(self, message: str, status_code: int = 400, details: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class AsaasClient:
    """Cliente wrapper para comunicação com o Asaas v3."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or settings.ASAAS_API_KEY
        self.base_url = (base_url or settings.ASAAS_API_URL).rstrip("/")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict[str, str]:
        return {
            "access_token": self.api_key or "",
            "Content-Type": "application/json",
            "User-Agent": "Lumina-SaaS-Billing/1.0",
        }

    def create_or_get_customer(
        self,
        name: str,
        email: str,
        cpf_cnpj: str | None = None,
        phone: str | None = None,
    ) -> str:
        """Cria ou busca cliente no Asaas pelo e-mail ou documento."""
        if not self.is_configured:
            # Modo mock simulado para desenvolvimento local sem chave do Asaas
            logger.info("Asaas mock: criando cliente local para %s (%s)", name, email)
            return f"cus_mock_{uuid4().hex[:12]}"

        with httpx.Client(base_url=self.base_url, headers=self._headers(), timeout=15.0) as client:
            # 1. Tenta buscar existente por email
            query_resp = client.get("/customers", params={"email": email.strip().lower()})
            if query_resp.is_success:
                data = query_resp.json()
                items = data.get("data", [])
                if items:
                    return str(items[0]["id"])

            # 2. Se não existir, cria novo
            payload = {
                "name": name.strip(),
                "email": email.strip().lower(),
            }
            if cpf_cnpj:
                payload["cpfCnpj"] = "".join(filter(str.isdigit, cpf_cnpj))
            if phone:
                payload["phone"] = phone.strip()

            create_resp = client.post("/customers", json=payload)
            if not create_resp.is_success:
                raise AsaasError(
                    f"Erro ao criar cliente no Asaas: {create_resp.text}",
                    status_code=create_resp.status_code,
                    details=create_resp.json() if create_resp.headers.get("content-type", "").startswith("application/json") else {},
                )
            return str(create_resp.json()["id"])

    def create_subscription(
        self,
        customer_id: str,
        value: Decimal,
        cycle: BillingCycle,
        next_due_date: date,
        billing_type: str = "UNDEFINED",
        description: str = "Assinatura Lumina — Gestão & Retenção",
    ) -> dict:
        """Cria assinatura recorrente no Asaas."""
        if not self.is_configured:
            logger.info(
                "Asaas mock: gerando assinatura local para customer %s, valor R$ %s, ciclo %s",
                customer_id,
                value,
                cycle,
            )
            mock_sub_id = f"sub_mock_{uuid4().hex[:12]}"
            return {
                "id": mock_sub_id,
                "customer": customer_id,
                "value": float(value),
                "nextDueDate": next_due_date.isoformat(),
                "cycle": cycle.value,
                "billingType": billing_type,
                "status": "ACTIVE",
                "invoiceUrl": f"https://sandbox.asaas.com/i/{mock_sub_id}",
            }

        payload = {
            "customer": customer_id,
            "billingType": billing_type,
            "value": float(value),
            "nextDueDate": next_due_date.isoformat(),
            "cycle": cycle.value,
            "description": description,
        }

        with httpx.Client(base_url=self.base_url, headers=self._headers(), timeout=20.0) as client:
            resp = client.post("/subscriptions", json=payload)
            if not resp.is_success:
                raise AsaasError(
                    f"Erro ao criar assinatura no Asaas: {resp.text}",
                    status_code=resp.status_code,
                    details=resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {},
                )
            return resp.json()

    def get_subscription_payments(self, subscription_id: str) -> list[dict]:
        """Obtém as cobranças de uma assinatura."""
        if not self.is_configured:
            return []

        with httpx.Client(base_url=self.base_url, headers=self._headers(), timeout=15.0) as client:
            resp = client.get(f"/subscriptions/{subscription_id}/payments")
            if not resp.is_success:
                return []
            return resp.json().get("data", [])

    def get_pix_qr_code(self, payment_id: str) -> dict:
        """Obtém o QR Code e payload copia-e-cola de uma cobrança Pix."""
        if not self.is_configured:
            return {
                "encodedImage": "",
                "payload": "00020126580014br.gov.bcb.pix0136mock-pix-payload-lumina",
                "expirationDate": "2026-12-31 23:59:59",
            }

        with httpx.Client(base_url=self.base_url, headers=self._headers(), timeout=15.0) as client:
            resp = client.get(f"/payments/{payment_id}/pixQrCode")
            if not resp.is_success:
                return {}
            return resp.json()
