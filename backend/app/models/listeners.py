"""Listener before_flush — PROÍBE alteração de campos congelados
(invariante I3, T-020b, backend/ENGENHARIA.md §4).

Listener é a ferramenta certa AQUI porque a regra é uma proibição
TRANSVERSAL — vale para todo caminho de código, inclusive um que
esqueçam de escrever. O CÁLCULO em si NÃO vive aqui (isso seria
domain/service, ver app/domain/financial/calculator.py e
app/services/sale_service.py) — este módulo só barra UPDATE nos campos
que o service já congelou no INSERT.

Importado por app/db/session.py para o listener ser registrado no
mesmo módulo que cria o engine (SQLAlchemy registra por Session class,
então basta importar uma vez no processo).
"""

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session as OrmSession

from app.models.sale import Sale

# Campos congelados no ato da venda (invariante I3) — nunca UPDATE
# depois do INSERT. cost_realized é a ÚNICA exceção intencional: muda
# quando sessões completam/expiram (§12.1) — por isso NÃO está aqui.
FROZEN_FIELDS: dict[type, tuple[str, ...]] = {
    Sale: (
        "items_total",
        "discount_amount",
        "gross_amount",
        "split_applied",
        "split_amount_applied",
        "split_base_applied",
        "fee_payer_applied",
        "fee_applied",
        "fee_amount_applied",
        "fee_amount_charged_applied",
        "cost_provisioned",
        # cost_realized: EXCLUÍDO de propósito — muda com o ciclo de
        # vida das sessões (COMPLETED/EXPIRED), não é congelado.
        "net_profit",
        "margin",
    ),
}


class ImmutableFieldError(Exception):
    pass


@event.listens_for(OrmSession, "before_flush")
def _bloqueia_alteracao_de_snapshot(session, flush_context, instances) -> None:
    for obj in session.dirty:
        frozen = FROZEN_FIELDS.get(type(obj))
        if not frozen:
            continue
        for field in frozen:
            hist = inspect(obj).attrs[field].history
            # deleted não-vazio = havia valor anterior = é UPDATE, não
            # o INSERT inicial (que só tem "added").
            if hist.has_changes() and hist.deleted:
                raise ImmutableFieldError(
                    f"{type(obj).__name__}.{field} é congelado (invariante I3). "
                    "Para corrigir, estorne e refaça — nunca UPDATE direto."
                )
