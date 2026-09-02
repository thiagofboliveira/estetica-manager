"""Conversão de fuso horário (invariante I4, MVP v6 §3).

Todo agrupamento por dia/mês converte para o fuso da PROFISSIONAL antes
de truncar — nunca trunca em UTC. Um atendimento às 22h em São Paulo
(01h UTC do dia seguinte) precisa contar como "hoje" para ela, senão o
erro aparece exatamente no fechamento do dia, quando ela olha o
dashboard ou registra a venda perto da meia-noite.
"""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo


def today_in_timezone(tz_name: str) -> date:
    """A data de "hoje" no fuso da profissional, não em UTC."""
    return datetime.now(ZoneInfo(tz_name)).date()


def utc_to_local_date(moment: datetime, tz_name: str) -> date:
    """Converte um instante (aware, qualquer fuso) para a data local da
    profissional — usar antes de truncar por dia (ex: agrupar sessões,
    filtrar vendas por período)."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(ZoneInfo(tz_name)).date()


def now_in_timezone(tz_name: str) -> datetime:
    """O instante "agora" no fuso da profissional, aware — usar para
    carimbar completed_at/contacted_at, nunca datetime.now(UTC) direto
    (mesma disciplina de today_in_timezone, invariante I4)."""
    return datetime.now(ZoneInfo(tz_name))
