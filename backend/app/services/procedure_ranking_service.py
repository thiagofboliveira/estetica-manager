"""ProcedureRankingService — orquestra GET /reports/procedures (MVP v6
§13 TASK-024).

Camada de orquestração (backend/ENGENHARIA.md §5): busca itens+vendas do
período, resolve nome do procedimento via ProcedureRepository, monta os
dataclasses puros de domain/financial/procedure_ranking, chama
build_procedure_ranking(). O CÁLCULO em si vive em domain/.
"""

from datetime import date

from app.core.tz import today_in_timezone
from app.domain.financial.period import ResolvedPeriod, resolve_period
from app.domain.financial.procedure_ranking import (
    ItemForRanking,
    ProcedureRankingRow,
    build_procedure_ranking,
)
from app.repositories.procedure import ProcedureRepository
from app.repositories.professional import ProfessionalRepository
from app.repositories.sale_item import SaleItemRepository


class ProcedureRankingService:
    def __init__(
        self,
        sale_item_repo: SaleItemRepository,
        procedure_repo: ProcedureRepository,
        professional_repo: ProfessionalRepository,
    ) -> None:
        self._sale_items = sale_item_repo
        self._procedures = procedure_repo
        self._professionals = professional_repo

    def get_ranking(
        self,
        *,
        filter_name: str,
        custom_from: date | None = None,
        custom_to: date | None = None,
    ) -> tuple[list[ProcedureRankingRow], ResolvedPeriod]:
        professional = self._professionals.get_current()
        today = today_in_timezone(professional.timezone)
        period = resolve_period(
            filter_name=filter_name, today=today,
            custom_from=custom_from, custom_to=custom_to,
        )

        pairs = self._sale_items.list_with_sale_totals_in_period(
            period.date_from, period.date_to
        )

        # Nome do procedimento: um procedimento arquivado ainda deve
        # aparecer no ranking histórico — o item já congelou o que
        # importa financeiramente (unit_price/unit_cost_estimated), só o
        # NOME é lido do cadastro atual (ou "(removido)" se não existir
        # mais o registro).
        procedure_names: dict = {}
        for item, _sale in pairs:
            if item.procedure_id not in procedure_names:
                proc = self._procedures.get(item.procedure_id)
                procedure_names[item.procedure_id] = (
                    proc.name if proc else "(procedimento removido)"
                )

        items = [
            ItemForRanking(
                procedure_id=item.procedure_id,
                procedure_name=procedure_names[item.procedure_id],
                unit_price=item.unit_price,
                quantity=item.quantity,
                unit_cost_estimated=item.unit_cost_estimated,
                discount_allocated=item.discount_allocated,
                sale_split_amount=sale.split_amount_applied,
                sale_fee_charged=sale.fee_amount_charged_applied,
                sale_line_totals_sum=sale.items_total,
            )
            for item, sale in pairs
        ]

        ranking = build_procedure_ranking(items)
        return ranking, period
