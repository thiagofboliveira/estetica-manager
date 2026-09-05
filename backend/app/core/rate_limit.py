"""Rate limit in-memory simples, por professional_id (AC-07) ou por IP
(S-04, rotas públicas sem professional_id — /system/setup, /dev/login).

Aceitável para MVP: um único processo, sem necessidade de coordenação
entre workers. Se o backend escalar para múltiplos processos, migrar
para um backend compartilhado (Redis).
"""

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from uuid import UUID


class InMemoryRateLimiter:
    def __init__(self, max_calls: int, window: timedelta) -> None:
        self._max_calls = max_calls
        self._window = window
        self._calls: dict[UUID | str, list[datetime]] = defaultdict(list)

    def check(self, key: UUID | str) -> timedelta | None:
        """Retorna None se a chamada é permitida, ou o tempo até a
        próxima chamada liberada se o limite foi excedido."""
        now = datetime.now(UTC)
        cutoff = now - self._window
        calls = [c for c in self._calls[key] if c > cutoff]

        if len(calls) >= self._max_calls:
            self._calls[key] = calls
            retry_after = calls[0] + self._window - now
            return retry_after

        calls.append(now)
        self._calls[key] = calls
        return None
