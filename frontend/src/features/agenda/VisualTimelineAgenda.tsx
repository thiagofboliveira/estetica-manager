import { useState, useMemo } from "react";
import type { AgendaItem, SessionStatus } from "./api";
import { formatLocalDate } from "@/lib/format/date";
import { IconCalendar, IconCheck, IconPlus, IconSparkles, IconAlertTriangle } from "@/ui/icons";
import styles from "./VisualTimelineAgenda.module.css";

interface Props {
  items: AgendaItem[];
  currentDateFrom: string;
  currentDateTo: string;
  onUpdateSessionStatus: (item: AgendaItem, status: SessionStatus) => void;
  onConvertBooking: (item: AgendaItem) => void;
  onBookSlot: (slotDateTimeISO: string) => void;
}

const OPERATING_HOURS = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20];

export function VisualTimelineAgenda({
  items,
  currentDateFrom,
  currentDateTo,
  onUpdateSessionStatus,
  onConvertBooking,
  onBookSlot,
}: Props) {
  const [viewType, setViewType] = useState<"timeline" | "list">("timeline");
  
  // Selected day inside the view range (defaults to today or currentDateFrom)
  const todayStr = formatLocalDate(new Date());
  const [selectedDate, setSelectedDate] = useState<string>(() => {
    return currentDateFrom <= todayStr && todayStr <= currentDateTo ? todayStr : currentDateFrom;
  });

  // Calculate 7-day range for day selector strip
  const daysList = useMemo(() => {
    const days: { dateStr: string; weekday: string; dayNum: string; count: number }[] = [];
    const start = new Date(currentDateFrom + "T00:00:00");
    const end = new Date(currentDateTo + "T23:59:59");

    const current = new Date(start);
    while (current <= end && days.length < 14) {
      const dateStr = formatLocalDate(current);
      const weekday = current.toLocaleDateString("pt-BR", { weekday: "short" }).replace(".", "");
      const dayNum = current.getDate().toString();

      // Count appointments on this day
      const count = items.filter((it) => {
        const itemDate = formatLocalDate(new Date(it.scheduled_at));
        return itemDate === dateStr;
      }).length;

      days.push({ dateStr, weekday, dayNum, count });
      current.setDate(current.getDate() + 1);
    }
    return days;
  }, [currentDateFrom, currentDateTo, items]);

  // Appointments on currently selected date
  const dayAppointments = useMemo(() => {
    return items.filter((it) => {
      const itemDate = formatLocalDate(new Date(it.scheduled_at));
      return itemDate === selectedDate;
    });
  }, [items, selectedDate]);

  // Group appointments by hour slot
  const appointmentsByHour = useMemo(() => {
    const map = new Map<number, AgendaItem[]>();
    for (const h of OPERATING_HOURS) {
      map.set(h, []);
    }

    for (const appt of dayAppointments) {
      const hour = new Date(appt.scheduled_at).getHours();
      const existing = map.get(hour) || [];
      existing.push(appt);
      map.set(hour, existing);
    }
    return map;
  }, [dayAppointments]);

  // Calculate occupancy statistics for the selected day
  const busyHoursCount = Array.from(appointmentsByHour.values()).filter((arr) => arr.length > 0).length;
  const totalSlots = OPERATING_HOURS.length;
  const occupancyPercentage = Math.round((busyHoursCount / totalSlots) * 100);

  // Navigate back/forward by 1 day
  function handleNavigateDay(delta: number) {
    const curr = new Date(selectedDate + "T00:00:00");
    curr.setDate(curr.getDate() + delta);
    setSelectedDate(formatLocalDate(curr));
  }

  const selectedDateObj = new Date(selectedDate + "T00:00:00");
  const selectedDateFormatted = selectedDateObj.toLocaleDateString("pt-BR", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  return (
    <div className={styles.container}>
      {/* Top Toolbar: View Switcher & Day Navigation */}
      <div className={styles.toolbar}>
        <div className={styles.viewSwitchGroup}>
          <button
            type="button"
            className={viewType === "timeline" ? `${styles.viewSwitchBtn} ${styles.viewSwitchBtnActive}` : styles.viewSwitchBtn}
            onClick={() => setViewType("timeline")}
          >
            <IconCalendar width="15" height="15" />
            <span>Grade Visual de Horários</span>
          </button>
          <button
            type="button"
            className={viewType === "list" ? `${styles.viewSwitchBtn} ${styles.viewSwitchBtnActive}` : styles.viewSwitchBtn}
            onClick={() => setViewType("list")}
          >
            <span>Lista Cronológica</span>
          </button>
        </div>

        <div className={styles.navigationBar}>
          <button
            type="button"
            className={styles.navBtn}
            onClick={() => handleNavigateDay(-1)}
            title="Dia anterior"
          >
            ←
          </button>
          <span className={styles.currentDateLabel}>
            {selectedDate === todayStr ? "Hoje, " : ""}
            {selectedDateObj.toLocaleDateString("pt-BR", { day: "numeric", month: "short" })}
          </span>
          <button
            type="button"
            className={styles.navBtn}
            onClick={() => handleNavigateDay(1)}
            title="Próximo dia"
          >
            →
          </button>
          {selectedDate !== todayStr && (
            <button
              type="button"
              className={styles.navBtn}
              onClick={() => setSelectedDate(todayStr)}
            >
              Hoje
            </button>
          )}
        </div>
      </div>

      {/* Day Selector Strip with Occupancy badges */}
      <div className={styles.dayStrip}>
        {daysList.map((day) => {
          const isActive = day.dateStr === selectedDate;
          const isToday = day.dateStr === todayStr;

          return (
            <div
              key={day.dateStr}
              className={isActive ? `${styles.dayStripCard} ${styles.dayStripCardActive}` : styles.dayStripCard}
              onClick={() => setSelectedDate(day.dateStr)}
            >
              <span className={styles.dayStripWeekday}>
                {isToday ? "Hoje" : day.weekday}
              </span>
              <span className={styles.dayStripDate}>{day.dayNum}</span>
              <span
                className={
                  day.count === 0
                    ? `${styles.dayStripOccupancy} ${styles.dayStripOccupancyFree}`
                    : `${styles.dayStripOccupancy} ${styles.dayStripOccupancyBusy}`
                }
              >
                {day.count === 0 ? "Livre" : `${day.count} agend.`}
              </span>
            </div>
          );
        })}
      </div>

      {/* Occupancy Indicator Bar */}
      <div className={styles.occupancyBar}>
        <div className={styles.occupancyInfo}>
          <span className={styles.occupancyLabel}>Ocupação em {selectedDateFormatted}:</span>
          <span
            className={
              occupancyPercentage >= 75
                ? `${styles.occupancyBadge} ${styles.occupancyBadgeHigh}`
                : occupancyPercentage >= 30
                ? `${styles.occupancyBadge} ${styles.occupancyBadgeNormal}`
                : `${styles.occupancyBadge} ${styles.occupancyBadgeLow}`
            }
          >
            {occupancyPercentage}% Ocupada ({busyHoursCount} de {totalSlots} horários)
          </span>
        </div>

        <div className={styles.occupancyProgressContainer}>
          <div className={styles.progressBarBg}>
            <div
              className={styles.progressBarFill}
              style={{ width: `${occupancyPercentage}%` }}
            />
          </div>
        </div>

        <div className={styles.legend}>
          <div className={styles.legendItem}>
            <span className={styles.legendDot} style={{ background: "var(--accent)" }} />
            <span>Sessão</span>
          </div>
          <div className={styles.legendItem}>
            <span className={styles.legendDot} style={{ background: "var(--warning)" }} />
            <span>Reserva</span>
          </div>
          <div className={styles.legendItem}>
            <span className={styles.legendDot} style={{ background: "var(--success)" }} />
            <span>Concluído</span>
          </div>
          <div className={styles.legendItem}>
            <span className={styles.legendDot} style={{ background: "var(--border-input)" }} />
            <span>Livre</span>
          </div>
        </div>
      </div>

      {/* VIEW 1: Visual Hourly Timeline Grid */}
      {viewType === "timeline" && (
        <div className={styles.timelineGridWrapper}>
          <div className={styles.timelineGrid}>
            {OPERATING_HOURS.map((hour) => {
              const hourAppointments = appointmentsByHour.get(hour) || [];
              const hourStr = `${hour.toString().padStart(2, "0")}:00`;
              const slotISO = `${selectedDate}T${hour.toString().padStart(2, "0")}:00`;

              return (
                <div key={hour} className={styles.timeRow}>
                  <div className={styles.timeCol}>
                    <span className={styles.timeLabel}>{hourStr}</span>
                    <span className={styles.timePeriod}>{hour < 12 ? "Manhã" : hour < 18 ? "Tarde" : "Noite"}</span>
                  </div>

                  <div className={styles.slotsCol}>
                    {hourAppointments.length === 0 ? (
                      <div
                        className={styles.freeSlot}
                        onClick={() => onBookSlot(slotISO)}
                      >
                        <span className={styles.freeSlotText}>
                          <IconSparkles width="14" height="14" style={{ color: "var(--text-muted)" }} />
                          <span>Horário Livre para Atendimento</span>
                        </span>
                        <button
                          type="button"
                          className={styles.freeSlotBtn}
                          onClick={(e) => {
                            e.stopPropagation();
                            onBookSlot(slotISO);
                          }}
                        >
                          <IconPlus width="13" height="13" />
                          <span>Agendar neste horário</span>
                        </button>
                      </div>
                    ) : (
                      hourAppointments.map((item) => {
                        const dt = new Date(item.scheduled_at);
                        const timeFormatted = dt.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });

                        let cardClass = styles.cardScheduled;
                        if (item.status === "COMPLETED") cardClass = styles.cardCompleted;
                        else if (item.status === "NO_SHOW") cardClass = styles.cardNoShow;
                        else if (item.type === "BOOKING") cardClass = styles.cardBooking;

                        return (
                          <div key={`${item.type}-${item.id}`} className={`${styles.appointmentCard} ${cardClass}`}>
                            <div className={styles.cardHeader}>
                              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                                <span style={{ fontSize: "13px", fontWeight: "700", color: "var(--text-h)" }}>{timeFormatted}</span>
                                <span className={styles.patientName}>{item.patient_name}</span>
                              </div>
                              <span className={styles.badgeModality}>
                                {item.modality === "REMOTE" ? "Remoto" : "Presencial"}
                              </span>
                            </div>

                            <div className={styles.cardBody}>
                              <span className={styles.procedureName}>{item.procedure_name}</span>
                              {item.type === "SESSION" && item.sequence_number && item.total_sessions && (
                                <span className={styles.sessionProgress}>
                                  Sessão {item.sequence_number} de {item.total_sessions}
                                </span>
                              )}
                              {item.type === "BOOKING" && (
                                <span className={styles.sessionProgress} style={{ color: "var(--warning)" }}>
                                  Reserva Provisória (Sem Venda)
                                </span>
                              )}
                              {item.note && (
                                <span className={styles.sessionProgress}>Obs: {item.note}</span>
                              )}
                            </div>

                            <div className={styles.cardActions}>
                              {item.type === "BOOKING" && (
                                <button
                                  type="button"
                                  className={styles.btnActionSmall}
                                  onClick={() => onConvertBooking(item)}
                                >
                                  💳 Converter em Venda
                                </button>
                              )}

                              {item.type === "SESSION" && item.status === "SCHEDULED" && (
                                <>
                                  <button
                                    type="button"
                                    className={styles.btnActionComplete}
                                    onClick={() => onUpdateSessionStatus(item, "COMPLETED")}
                                  >
                                    <IconCheck width="12" height="12" />
                                    <span>Concluir</span>
                                  </button>
                                  <button
                                    type="button"
                                    className={styles.btnActionSmall}
                                    onClick={() => onUpdateSessionStatus(item, "NO_SHOW")}
                                  >
                                    <IconAlertTriangle width="12" height="12" />
                                    <span>Falta</span>
                                  </button>
                                </>
                              )}

                              {item.status === "COMPLETED" && (
                                <span style={{ fontSize: "12px", color: "var(--success)", fontWeight: "600", display: "inline-flex", alignItems: "center", gap: "4px" }}>
                                  <IconCheck width="14" height="14" /> Concluído
                                </span>
                              )}

                              {item.status === "NO_SHOW" && (
                                <span style={{ fontSize: "12px", color: "var(--danger)", fontWeight: "600" }}>
                                  Não compareceu (Falta)
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* VIEW 2: Chronological Detailed List */}
      {viewType === "list" && (
        <ul className="list agenda-list">
          {items.length === 0 ? (
            <li className="list__item" style={{ padding: "32px", textAlign: "center", color: "var(--text-muted)" }}>
              Nenhum agendamento encontrado no período.
            </li>
          ) : (
            items.map((item) => {
              const dt = new Date(item.scheduled_at);
              const timeStr = dt.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
              const dateFormatted = dt.toLocaleDateString("pt-BR", { weekday: "short", day: "numeric", month: "short" });

              return (
                <li key={`${item.type}-${item.id}`} className="list__item agenda-item">
                  <div className="agenda-item__time-block" style={{ padding: "14px", display: "flex", flexDirection: "column", gap: "2px" }}>
                    <span style={{ fontSize: "16px", fontWeight: "700", color: "var(--text-h)" }}>{timeStr}</span>
                    <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>{dateFormatted}</span>
                  </div>

                  <div className="agenda-item__main" style={{ flex: 1, padding: "14px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap", marginBottom: "4px" }}>
                      <strong style={{ fontSize: "15px", color: "var(--text-h)" }}>{item.patient_name}</strong>
                      <span className="badge badge--neutral">
                        {item.modality === "REMOTE" ? "Remoto" : "Presencial"}
                      </span>
                      {item.type === "BOOKING" && (
                        <span className="badge badge--warning">Reserva Provisória</span>
                      )}
                      {item.type === "SESSION" && item.sequence_number && item.total_sessions && (
                        <span className="badge badge--success">
                          Sessão {item.sequence_number} de {item.total_sessions}
                        </span>
                      )}
                    </div>

                    <div style={{ fontSize: "13.5px", color: "var(--text)" }}>
                      <span>{item.procedure_name}</span>
                      {item.note && <span style={{ color: "var(--text-muted)", marginLeft: "8px" }}>Obs: {item.note}</span>}
                    </div>
                  </div>

                  <div style={{ padding: "14px", display: "flex", gap: "8px", alignItems: "center" }}>
                    {item.type === "BOOKING" && (
                      <button
                        type="button"
                        onClick={() => onConvertBooking(item)}
                        className="button button--secondary tap-target"
                      >
                        💳 Converter em Venda
                      </button>
                    )}

                    {item.type === "SESSION" && item.status === "SCHEDULED" && (
                      <div style={{ display: "flex", gap: "6px" }}>
                        <button
                          type="button"
                          onClick={() => onUpdateSessionStatus(item, "COMPLETED")}
                          className="button tap-target"
                        >
                          <IconCheck width="14" height="14" />
                          <span>Concluir</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => onUpdateSessionStatus(item, "NO_SHOW")}
                          className="button button--ghost tap-target"
                        >
                          Falta
                        </button>
                      </div>
                    )}
                  </div>
                </li>
              );
            })
          )}
        </ul>
      )}
    </div>
  );
}
