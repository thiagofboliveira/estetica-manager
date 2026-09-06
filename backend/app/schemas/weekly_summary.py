"""Schemas para o resumo semanal (A-12 / V5-01 / V5-02)."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class WeeklySummaryOut(BaseModel):
    professional_name: str
    period_start: date
    period_end: date
    gross_revenue: Decimal
    net_profit: Decimal
    sales_count: int
    pending_opportunities_count: int
    weekly_summary_enabled: bool
    whatsapp_message: str
    whatsapp_url: str | None = None
    unsubscribe_url: str


class WeeklySummarySettingsUpdate(BaseModel):
    weekly_summary_enabled: bool


class WeeklySummaryUnsubscribeOut(BaseModel):
    status: str
    message: str
