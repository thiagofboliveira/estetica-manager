"""EventService — emite eventos de ativação de forma idempotente (G-13).

"Um sistema que não se mede não pode ser melhorado" — antes desta task
não havia nenhuma tabela de eventos, funil ou cohort (L-4 do
docs/README.md). O objetivo aqui é o mínimo que já dá sinal de
ativação: os eventos "first_*" citados em G-14 (time-to-value).

Escopo desta versão: emitir e listar. G-14 (funil agregado, painel de
super-admin) fica para depois — exigiria a mesma decisão de RLS
cross-clínica que S-02 registrou como pendente.
"""

from app.domain.events import EventName
from app.models.event import Event
from app.repositories.event import EventRepository


class EventService:
    def __init__(self, event_repo: EventRepository) -> None:
        self._events = event_repo

    def track_first(self, name: EventName, payload: dict | None = None) -> None:
        """Emite o evento só na primeira ocorrência — chamadas
        subsequentes são no-op silencioso. Não levanta em caso de falha
        do próprio tracking: perder um evento nunca pode quebrar o
        fluxo de negócio que o originou (ex.: registrar uma venda não
        pode falhar porque o evento de ativação deu erro)."""
        try:
            if self._events.has_event(name.value):
                return
            self._events.add(Event(name=name.value, payload=payload))
            self._events.flush()
        except Exception:
            # Melhor esforço — telemetria nunca derruba o caminho principal.
            pass

    def track(self, name: EventName, payload: dict | None = None) -> None:
        """Emite sempre (não é "first_*") — contagem repetida (ex: booking público)."""
        try:
            self._events.add(Event(name=name.value, payload=payload))
            self._events.flush()
        except Exception:
            pass

    def count_by_name(self, name: str | EventName) -> int:
        """Retorna o número de ocorrências de um evento."""
        try:
            val = name.value if isinstance(name, EventName) else name
            return self._events.count_by_name(val)
        except Exception:
            return 0

    def get_time_to_first_profit_seconds(self) -> float | None:
        """A-07 / G-14: Calcula o time-to-value em segundos (primeiro login → primeiro lucro na tela)."""
        try:
            login_event = self._events.get_first_by_name(EventName.FIRST_LOGIN.value)
            profit_event = self._events.get_first_by_name(EventName.FIRST_PROFIT_VIEWED.value)
            if not login_event or not profit_event:
                return None
            delta = (profit_event.created_at - login_event.created_at).total_seconds()
            return max(0.0, delta)
        except Exception:
            return None

