import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { formatLocalDate } from "@/lib/format/date";
import type { AgendaItem, SessionStatus } from "./api";
import { useAgenda, useScheduleSession } from "./hooks";
import { VisualTimelineAgenda } from "./VisualTimelineAgenda";
import { NewBookingModal } from "./NewBookingModal";

type ViewMode = "today" | "week" | "custom";

export function AgendaView() {
  const navigate = useNavigate();
  const scheduleSession = useScheduleSession();

  const [mode, setMode] = useState<ViewMode>("week");
  const [slotToBook, setSlotToBook] = useState<string | null>(null);

  const todayStr = formatLocalDate(new Date());
  const next7Days = new Date();
  next7Days.setDate(next7Days.getDate() + 7);
  const next7DaysStr = formatLocalDate(next7Days);

  const [customFrom, setCustomFrom] = useState(todayStr);
  const [customTo, setCustomTo] = useState(next7DaysStr);

  const dateFrom = mode === "today" ? todayStr : mode === "week" ? todayStr : customFrom;
  const dateTo = mode === "today" ? todayStr : mode === "week" ? next7DaysStr : customTo;

  const query = useAgenda(dateFrom, dateTo);

  async function handleUpdateSessionStatus(session: AgendaItem, status: SessionStatus) {
    const statusLabel = status === "COMPLETED" ? "Concluída" : "Falta (No-show)";
    if (!window.confirm(`Deseja marcar esta sessão como ${statusLabel}?`)) {
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
      <div className="agenda-view__controls" style={{ marginBottom: "18px" }}>
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
        skeleton={<p>Carregando agenda visual…</p>}
        empty={null}
        isEmpty={() => false}
      >
        {(items) => (
          <VisualTimelineAgenda
            items={items}
            currentDateFrom={dateFrom}
            currentDateTo={dateTo}
            onUpdateSessionStatus={handleUpdateSessionStatus}
            onConvertBooking={handleConvertBooking}
            onBookSlot={(slotDateTimeISO) => setSlotToBook(slotDateTimeISO)}
          />
        )}
      </AsyncBoundary>

      {slotToBook && (
        <NewBookingModal
          initialDateTime={slotToBook}
          onClose={() => setSlotToBook(null)}
        />
      )}
    </div>
  );
}
