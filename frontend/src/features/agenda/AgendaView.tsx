import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { EmptyState } from "@/ui/EmptyState";
import type { AgendaItem, SessionStatus } from "./api";
import { useAgenda, useScheduleSession } from "./hooks";

type ViewMode = "today" | "week" | "custom";

export function AgendaView() {
  const navigate = useNavigate();
  const scheduleSession = useScheduleSession();

  const [mode, setMode] = useState<ViewMode>("today");

  const todayStr = new Date().toISOString().slice(0, 10);
  const next7Days = new Date();
  next7Days.setDate(next7Days.getDate() + 7);
  const next7DaysStr = next7Days.toISOString().slice(0, 10);

  const [customFrom, setCustomFrom] = useState(todayStr);
  const [customTo, setCustomTo] = useState(next7DaysStr);

  const dateFrom = mode === "today" ? todayStr : mode === "week" ? todayStr : customFrom;
  const dateTo = mode === "today" ? todayStr : mode === "week" ? next7DaysStr : customTo;

  const query = useAgenda(dateFrom, dateTo);

  async function handleUpdateSessionStatus(session: AgendaItem, status: SessionStatus) {
    if (!window.confirm(`Deseja marcar esta sessão como ${status === "COMPLETED" ? "Concluída" : "Falta (No-show)"}?`)) {
      return;
    }
    try {
      await scheduleSession.mutateAsync({
        id: session.id,
        payload: { status },
      });
    } catch {
      alert("Não foi possível atualizar o status da sessão.");
    }
  }

  function handleConvertBooking(booking: AgendaItem) {
    navigate(`/vendas/nova?booking_id=${booking.id}&patient_name=${encodeURIComponent(booking.patient_name)}`);
  }

  return (
    <div className="agenda-view">
      <div className="agenda-view__controls">
        <div className="tab-group" role="group" aria-label="Período da agenda">
          <button
            type="button"
            className="tab-button tap-target"
            aria-selected={mode === "today"}
            onClick={() => setMode("today")}
          >
            Hoje
          </button>
          <button
            type="button"
            className="tab-button tap-target"
            aria-selected={mode === "week"}
            onClick={() => setMode("week")}
          >
            Próximos 7 dias
          </button>
          <button
            type="button"
            className="tab-button tap-target"
            aria-selected={mode === "custom"}
            onClick={() => setMode("custom")}
          >
            Personalizado
          </button>
        </div>

        {mode === "custom" && (
          <div className="form__row" style={{ marginTop: "12px" }}>
            <label className="form__field">
              <span>De</span>
              <input type="date" value={customFrom} onChange={(e) => setCustomFrom(e.target.value)} />
            </label>
            <label className="form__field">
              <span>Até</span>
              <input type="date" value={customTo} onChange={(e) => setCustomTo(e.target.value)} />
            </label>
          </div>
        )}
      </div>

      <AsyncBoundary
        query={query}
        skeleton={<p>Carregando agenda…</p>}
        empty={
          <EmptyState
            tone="good"
            title="Nenhum atendimento agendado no período"
            body="Sua agenda está livre para estas datas."
          />
        }
        isEmpty={(items) => items.length === 0}
      >
        {(items) => (
          <ul className="list agenda-list">
            {items.map((item) => {
              const dt = new Date(item.scheduled_at);
              const timeStr = dt.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
              const dateFormatted = dt.toLocaleDateString("pt-BR", { weekday: "short", day: "numeric", month: "short" });

              return (
                <li key={`${item.type}-${item.id}`} className="list__item agenda-item">
                  <div className="agenda-item__time-block">
                    <span className="agenda-item__time">{timeStr}</span>
                    <span className="agenda-item__date">{dateFormatted}</span>
                  </div>

                  <div className="agenda-item__main">
                    <div className="agenda-item__header">
                      <strong className="agenda-item__patient">{item.patient_name}</strong>
                      <div className="agenda-item__badges">
                        {/* F-017a: modalidade com ícone + texto */}
                        <span className="badge badge--neutral">
                          {item.modality === "REMOTE" ? "💻 Remoto" : "📍 Presencial"}
                        </span>
                        {item.type === "BOOKING" && (
                          <span className="badge badge--accent">Reserva Provisória</span>
                        )}
                        {item.type === "SESSION" && item.sequence_number && item.total_sessions && (
                          <span className="badge badge--success">
                            Sessão {item.sequence_number} de {item.total_sessions}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="agenda-item__details">
                      <span className="agenda-item__proc">{item.procedure_name}</span>
                      {item.note && <span className="agenda-item__note">Obs: {item.note}</span>}
                    </div>
                  </div>

                  <div className="agenda-item__actions">
                    {item.type === "BOOKING" && (
                      <button
                        type="button"
                        onClick={() => handleConvertBooking(item)}
                        className="button button--secondary tap-target"
                      >
                        💳 Converter em Venda
                      </button>
                    )}

                    {item.type === "SESSION" && item.status === "SCHEDULED" && (
                      <div className="agenda-item__btn-group">
                        <button
                          type="button"
                          onClick={() => handleUpdateSessionStatus(item, "COMPLETED")}
                          className="button tap-target"
                          title="Marcar sessão como realizada"
                        >
                          ✓ Concluir
                        </button>
                        <button
                          type="button"
                          onClick={() => handleUpdateSessionStatus(item, "NO_SHOW")}
                          className="button button--ghost tap-target"
                          title="Paciente não compareceu"
                        >
                          Falta
                        </button>
                      </div>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </AsyncBoundary>
    </div>
  );
}
