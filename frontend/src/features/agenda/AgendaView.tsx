import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { AsyncBoundary } from "@/ui/AsyncBoundary";
import { formatLocalDate } from "@/lib/format/date";
import { useAuth } from "@/lib/auth/AuthContext";
import { ClinicScopeSelector, type ClinicScopeValue } from "@/features/clinic-management/ClinicScopeSelector";
import type { AgendaItem, SessionStatus } from "./api";
import { useAgenda, useScheduleSession } from "./hooks";
import { VisualTimelineAgenda } from "./VisualTimelineAgenda";
import { NewBookingModal } from "./NewBookingModal";

type ViewMode = "today" | "week" | "month" | "custom";

// Grade do calendário mensal mostra semanas completas, então o range
// consultado precisa incluir os dias de padding do mês anterior/seguinte
// que aparecem na mesma semana do dia 1 e do último dia do mês.
function getMonthGridRange(reference: Date): { from: string; to: string } {
  const firstOfMonth = new Date(reference.getFullYear(), reference.getMonth(), 1);
  const lastOfMonth = new Date(reference.getFullYear(), reference.getMonth() + 1, 0);

  const gridStart = new Date(firstOfMonth);
  gridStart.setDate(gridStart.getDate() - gridStart.getDay());

  const gridEnd = new Date(lastOfMonth);
  gridEnd.setDate(gridEnd.getDate() + (6 - gridEnd.getDay()));

  return { from: formatLocalDate(gridStart), to: formatLocalDate(gridEnd) };
}

export function AgendaView() {
  const navigate = useNavigate();
  const scheduleSession = useScheduleSession();
  const { user } = useAuth();

  const [clinicScope, setClinicScope] = useState<ClinicScopeValue>(() => ({
    scope: user?.role === "admin" && user?.clinic_id ? "clinic" : "me",
  }));

  const [mode, setMode] = useState<ViewMode>("week");
  const [slotToBook, setSlotToBook] = useState<string | null>(null);
  const [monthCursor, setMonthCursor] = useState(() => new Date());

  const todayStr = formatLocalDate(new Date());
  const next7Days = new Date();
  next7Days.setDate(next7Days.getDate() + 7);
  const next7DaysStr = formatLocalDate(next7Days);

  const [customFrom, setCustomFrom] = useState(todayStr);
  const [customTo, setCustomTo] = useState(next7DaysStr);

  const monthGridRange = getMonthGridRange(monthCursor);

  const dateFrom =
    mode === "today" ? todayStr : mode === "week" ? todayStr : mode === "month" ? monthGridRange.from : customFrom;
  const dateTo =
    mode === "today" ? todayStr : mode === "week" ? next7DaysStr : mode === "month" ? monthGridRange.to : customTo;

  const query = useAgenda(dateFrom, dateTo, {
    scope: clinicScope.scope,
    professional_id: clinicScope.professional_id,
  });

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
    const params = new URLSearchParams();
    params.set("booking_id", booking.id);
    if (booking.patient_id) {
      params.set("patient_id", booking.patient_id);
    }
    if (booking.patient_name) {
      params.set("patient_name", booking.patient_name);
    }
    if (booking.procedure_id) {
      params.set("procedure_id", booking.procedure_id);
    }
    navigate(`/vendas/nova?${params.toString()}`);
  }

  return (
    <div className="agenda-view">
      <div className="agenda-view__controls" style={{ marginBottom: "18px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
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
            aria-selected={mode === "month"}
            onClick={() => {
              setMonthCursor(new Date());
              setMode("month");
            }}
          >
            Mês
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

        <ClinicScopeSelector
          value={clinicScope}
          onChange={setClinicScope}
        />

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
            defaultViewType={mode === "month" ? "month" : "timeline"}
            monthCursor={mode === "month" ? monthCursor : undefined}
            onNavigateMonth={(delta) => {
              setMonthCursor((prev) => new Date(prev.getFullYear(), prev.getMonth() + delta, 1));
            }}
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
