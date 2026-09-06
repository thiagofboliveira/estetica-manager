"""WeeklySummaryService — Geração do resumo semanal e gestão de opt-in (A-12, V5-01, V5-02).

Invariantes:
- I1: Lucro líquido das vendas é calculado via motor de lucro (calculate_sale/Sale.net_profit),
  nunca aproximado ou calculado no cliente.
- I4: Período da semana passada é calculado no fuso horário da profissional (timezone).
- I7: Se não houver atendimentos ou lucros, valores zerados são exibidos explicitamente.
"""

import re
import urllib.parse
from datetime import date, timedelta
from decimal import Decimal

from app.core.config import settings
from app.core.tz import today_in_timezone
from app.models.professional import Professional
from app.repositories.professional import ProfessionalRepository
from app.repositories.return_opportunity import ReturnOpportunityRepository
from app.repositories.sale import SaleRepository
from app.schemas.weekly_summary import WeeklySummaryOut


def calculate_last_week_bounds(ref_date: date) -> tuple[date, date]:
    """Retorna (segunda_anterior, domingo_anterior) relativo a ref_date."""
    current_monday = ref_date - timedelta(days=ref_date.weekday())
    last_monday = current_monday - timedelta(days=7)
    last_sunday = current_monday - timedelta(days=1)
    return last_monday, last_sunday


def format_weekly_summary_message(
    professional: Professional,
    period_start: date,
    period_end: date,
    gross_revenue: Decimal,
    net_profit: Decimal,
    sales_count: int,
    pending_opportunities_count: int,
    unsubscribe_url: str,
) -> str:
    start_str = period_start.strftime("%d/%m")
    end_str = period_end.strftime("%d/%m")
    return (
        f"📊 *Resumo da Semana — Lumina Estética*\n\n"
        f"Olá, {professional.name}! Aqui está o balanço da sua semana passada "
        f"({start_str} a {end_str}):\n\n"
        f"💰 *Faturado:* R$ {gross_revenue:.2f}\n"
        f"📈 *Lucro real:* R$ {net_profit:.2f}\n"
        f"✨ *Atendimentos:* {sales_count}\n"
        f"🎯 *Pacientes para chamar esta semana:* {pending_opportunities_count}\n\n"
        f"Acesse seu painel completo no sistema: {settings.FRONTEND_URL}/dashboard\n\n"
        f"---\n"
        f"Para pausar o envio deste resumo: {unsubscribe_url}"
    )


class WeeklySummaryService:
    def __init__(
        self,
        sale_repo: SaleRepository,
        return_opp_repo: ReturnOpportunityRepository,
        professional_repo: ProfessionalRepository,
    ) -> None:
        self._sales = sale_repo
        self._opps = return_opp_repo
        self._professionals = professional_repo

    def get_summary(
        self,
        reference_date: date | None = None,
        use_current_week: bool = False,
    ) -> WeeklySummaryOut:
        professional = self._professionals.get_current()
        today = reference_date or today_in_timezone(professional.timezone)

        if use_current_week:
            current_monday = today - timedelta(days=today.weekday())
            period_start = current_monday
            period_end = today
        else:
            period_start, period_end = calculate_last_week_bounds(today)

        sales = self._sales.list_in_period(period_start, period_end)
        gross_revenue = sum((s.gross_amount for s in sales), Decimal("0.00"))
        net_profit = sum((s.net_profit for s in sales), Decimal("0.00"))
        sales_count = len(sales)

        active_opps = self._opps.list_active()
        pending_opportunities_count = len(active_opps)

        unsubscribe_url = (
            f"{settings.FRONTEND_URL}/api/v1/public/weekly-summary/unsubscribe"
            f"?token={professional.weekly_summary_token}"
        )

        whatsapp_message = format_weekly_summary_message(
            professional=professional,
            period_start=period_start,
            period_end=period_end,
            gross_revenue=gross_revenue,
            net_profit=net_profit,
            sales_count=sales_count,
            pending_opportunities_count=pending_opportunities_count,
            unsubscribe_url=unsubscribe_url,
        )

        whatsapp_url = None
        if professional.phone:
            clean_phone = re.sub(r"\D", "", professional.phone)
            if clean_phone:
                encoded_msg = urllib.parse.quote(whatsapp_message)
                whatsapp_url = f"https://wa.me/{clean_phone}?text={encoded_msg}"

        return WeeklySummaryOut(
            professional_name=professional.name,
            period_start=period_start,
            period_end=period_end,
            gross_revenue=gross_revenue,
            net_profit=net_profit,
            sales_count=sales_count,
            pending_opportunities_count=pending_opportunities_count,
            weekly_summary_enabled=professional.weekly_summary_enabled,
            whatsapp_message=whatsapp_message,
            whatsapp_url=whatsapp_url,
            unsubscribe_url=unsubscribe_url,
        )

    def update_settings(self, enabled: bool) -> Professional:
        return self._professionals.update_weekly_summary_settings(enabled)
