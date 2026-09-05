import { useEffect, useState } from "react";
import { useParams, useSearchParams, Link } from "react-router-dom";
import {
  publicBookingApi,
  type PublicBooking,
} from "./api";
import styles from "./BookingManagementPage.module.css";

export function BookingManagementPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";

  const [loading, setLoading] = useState(true);
  const [booking, setBooking] = useState<PublicBooking | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Estados de Remarcação
  const [isRescheduling, setIsRescheduling] = useState(false);
  const [newDate, setNewDate] = useState<string>(() => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.toISOString().split("T")[0];
  });
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [availableSlots, setAvailableSlots] = useState<string[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
  const [rescheduling, setRescheduling] = useState(false);
  const [rescheduleError, setRescheduleError] = useState<string | null>(null);

  // Estados de Cancelamento
  const [cancelling, setCancelling] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!id || !token) {
      setError("Link de agendamento incompleto ou inválido.");
      setLoading(false);
      return;
    }

    publicBookingApi
      .getBooking(id, token)
      .then((data) => setBooking(data))
      .catch((err) => setError(err.message || "Agendamento não encontrado."))
      .finally(() => setLoading(false));
  }, [id, token]);

  // Carrega horários ao abrir modo remarcação
  useEffect(() => {
    if (!isRescheduling || !booking?.professional_slug || !newDate) return;

    setLoadingSlots(true);
    setSelectedSlot(null);
    publicBookingApi
      .getSlots(booking.professional_slug, newDate)
      .then((slots) => {
        setAvailableSlots(slots);
        if (slots.length > 0) setSelectedSlot(slots[0]);
      })
      .catch(() => setAvailableSlots([]))
      .finally(() => setLoadingSlots(false));
  }, [isRescheduling, booking?.professional_slug, newDate]);

  const handleConfirmReschedule = async () => {
    if (!id || !token || !newDate || !selectedSlot) return;

    setRescheduling(true);
    setRescheduleError(null);

    try {
      const scheduledDateTime = `${newDate}T${selectedSlot}:00Z`;
      const updated = await publicBookingApi.rescheduleBooking(id, token, {
        scheduled_at: scheduledDateTime,
      });
      setBooking(updated);
      setIsRescheduling(false);
    } catch (err: unknown) {
      const error = err as Error;
      setRescheduleError(error.message || "Não foi possível remarcar para este horário.");
    } finally {
      setRescheduling(false);
    }
  };

  const handleCancelBooking = async () => {
    if (!id || !token) return;
    if (!window.confirm("Deseja realmente cancelar este agendamento?")) return;

    setCancelling(true);
    try {
      const updated = await publicBookingApi.cancelBooking(id, token);
      setBooking(updated);
    } catch (err: unknown) {
      const error = err as Error;
      alert(error.message || "Erro ao cancelar agendamento.");
    } finally {
      setCancelling(false);
    }
  };

  const copyShareLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const formatScheduledDateTime = (iso: string) => {
    try {
      const date = new Date(iso);
      return date.toLocaleString("pt-BR", {
        weekday: "short",
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  };

  if (loading) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.container} style={{ textAlign: "center", paddingTop: "80px" }}>
          <p style={{ color: "var(--text-muted)" }}>Carregando dados do agendamento...</p>
        </div>
      </div>
    );
  }

  if (error || !booking) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.container} style={{ textAlign: "center", paddingTop: "80px" }}>
          <div className={styles.errorBanner}>
            {error || "Agendamento não encontrado."}
          </div>
        </div>
      </div>
    );
  }

  const isCancelled = booking.status === "CANCELLED";

  // Link para Google Agenda
  const getGoogleCalendarUrl = () => {
    const start = new Date(booking.scheduled_at);
    const end = new Date(start.getTime() + 60 * 60 * 1000); // 1 hora
    const formatGCal = (d: Date) => d.toISOString().replace(/-|:|\.\d\d\d/g, "");

    const title = encodeURIComponent(
      `Procedimento: ${booking.procedure_name || "Estética"} com ${booking.professional_name}`
    );
    const details = encodeURIComponent(
      `Agendamento confirmado no Lumina Estética Manager.\nPaciente: ${booking.patient_name}`
    );

    return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${formatGCal(
      start
    )}/${formatGCal(end)}&details=${details}`;
  };

  return (
    <div className={styles.wrapper}>
      <div className={styles.container}>
        {/* Card de Status */}
        <div className={styles.successCard}>
          <div
            className={`${styles.iconCircle} ${
              isCancelled ? styles.cancelledCircle : ""
            }`}
          >
            {isCancelled ? "✕" : "✓"}
          </div>
          <h1 className={styles.title}>
            {isCancelled ? "Agendamento Cancelado" : "Agendamento Confirmado!"}
          </h1>
          <p className={styles.subtitle}>
            {isCancelled
              ? "Este horário foi liberado com sucesso."
              : "Seu horário está reservado com exclusividade."}
          </p>
        </div>

        {/* Detalhes da Reserva */}
        <div className={styles.detailsCard}>
          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Profissional</span>
            <span className={styles.detailValue}>{booking.professional_name}</span>
          </div>

          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Procedimento</span>
            <span className={styles.detailValue}>{booking.procedure_name || "Procedimento"}</span>
          </div>

          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Data e Horário</span>
            <span className={styles.detailValue}>
              {formatScheduledDateTime(booking.scheduled_at)}
            </span>
          </div>

          <div className={styles.detailRow}>
            <span className={styles.detailLabel}>Paciente</span>
            <span className={styles.detailValue}>{booking.patient_name}</span>
          </div>

          {booking.procedure_price && (
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Valor Previsto</span>
              <span className={styles.detailValue} style={{ color: "var(--accent)" }}>
                R$ {parseFloat(booking.procedure_price).toFixed(2).replace(".", ",")}
              </span>
            </div>
          )}
        </div>

        {/* Caixa de Remarcação */}
        {isRescheduling && !isCancelled && (
          <div className={styles.rescheduleBox}>
            <h3 style={{ margin: 0, fontSize: "1rem", color: "var(--text-h)" }}>
              Escolha uma nova data e horário
            </h3>

            <input
              type="date"
              style={{
                padding: "10px",
                borderRadius: "8px",
                border: "1px solid var(--border)",
                fontSize: "1rem",
              }}
              value={newDate}
              min={new Date().toISOString().split("T")[0]}
              onChange={(e) => setNewDate(e.target.value)}
            />

            {loadingSlots ? (
              <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
                Verificando horários livres...
              </p>
            ) : availableSlots.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
                Sem vagas disponíveis neste dia. Escolha outra data.
              </p>
            ) : (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(80px, 1fr))",
                  gap: "8px",
                }}
              >
                {availableSlots.map((slot) => (
                  <button
                    type="button"
                    key={slot}
                    onClick={() => setSelectedSlot(slot)}
                    style={{
                      padding: "8px",
                      borderRadius: "6px",
                      border: "1.5px solid",
                      borderColor: selectedSlot === slot ? "var(--accent)" : "var(--border)",
                      background: selectedSlot === slot ? "var(--accent)" : "var(--bg-card)",
                      color: selectedSlot === slot ? "#ffffff" : "var(--text-h)",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    {slot}
                  </button>
                ))}
              </div>
            )}

            {rescheduleError && <div className={styles.errorBanner}>{rescheduleError}</div>}

            <div style={{ display: "flex", gap: "10px", marginTop: "6px" }}>
              <button
                type="button"
                className={styles.primaryBtn}
                style={{ flex: 1 }}
                onClick={handleConfirmReschedule}
                disabled={rescheduling || !selectedSlot}
              >
                {rescheduling ? "Salvando..." : "Confirmar Novo Horário"}
              </button>
              <button
                type="button"
                className={styles.secondaryBtn}
                onClick={() => setIsRescheduling(false)}
              >
                Voltar
              </button>
            </div>
          </div>
        )}

        {/* Botões de Ação */}
        {!isCancelled && !isRescheduling && (
          <div className={styles.actionGrid}>
            <a
              href={getGoogleCalendarUrl()}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.primaryBtn}
            >
              📅 Adicionar ao Google Agenda
            </a>

            <button type="button" className={styles.secondaryBtn} onClick={copyShareLink}>
              {copied ? "✓ Link copiado para a área de transferência!" : "🔗 Salvar Link Deste Agendamento"}
            </button>

            <button
              type="button"
              className={styles.secondaryBtn}
              onClick={() => setIsRescheduling(true)}
            >
              🔄 Remarcar Data / Horário
            </button>

            <button
              type="button"
              className={styles.dangerBtn}
              onClick={handleCancelBooking}
              disabled={cancelling}
            >
              {cancelling ? "Cancelando..." : "Cancelar Agendamento"}
            </button>
          </div>
        )}

        {isCancelled && booking.professional_slug && (
          <Link
            to={`/agendar/${booking.professional_slug}`}
            className={styles.primaryBtn}
            style={{ textAlign: "center", display: "block" }}
          >
            Fazer um Novo Agendamento
          </Link>
        )}

        <div className={styles.infoNotice}>
          💡 <strong>Dica:</strong> Guarde este link nos seus favoritos ou no WhatsApp para poder consultar, remarcar ou cancelar seu agendamento a qualquer momento.
        </div>
      </div>
    </div>
  );
}
